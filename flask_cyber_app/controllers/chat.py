import time
from flask import request, session
from flask_socketio import emit
from flask_cyber_app.models.models import Session, db, User, Chat, ChatRecipient
from flask_cyber_app.socket_connection.channel_manager import ChannelManager
from flask_cyber_app.utils.cache_utils import CacheUtils
from flask_cyber_app.utils.security_utils import SecurityUtils


class ChatController:
    def __init__(self, socketio):
        self.socketio = socketio
        self.socket_manager = ChannelManager()  # Initialize the ChannelManager
        self.register_events()
        self.cache_utils = CacheUtils()
        self.events_registered = False

    def register_events(self):
        self.socketio.on_event("key_exchange_init", self.handle_key_exchange_init)
        print("key_exchange_init")
        self.socketio.on_event("send_message", self.handle_message)
        print("send_message")
        self.socketio.on_event("connect", self.handle_connect)
        print("connect event")

    def handle_connect(self):
        """Handles a new WebSocket connection and stores the socket ID."""
        session_id = session.get("session_id")
        username = self.cache_utils.retrieve(f"current_user_name_{session_id}")
        self.cache_utils.store(f"current_socket_{session_id}", request.sid)

        if session_id:
            active_session = Session.query.get(session_id)
            if active_session:
                active_session.socket_id = request.sid  # Set socket ID here
                db.session.commit()
                print(f"Socket ID {request.sid} stored for session {session_id}")
                self.socketio.emit('connect_server', {'username': username}, to=request.sid)

    def handle_key_exchange_init(self, data):
        """
        Handle the initialization of key exchange.
        Generates and sends the server's public key to the client.
        """
        try:
            print(data)

            # Define strategy for handling different states
            state_handlers = {
                'recipient_process_secret_false': self._handle_recipient_process_secret_false,
                'sender_process_secret_false_recipient_true': self._handle_sender_process_secret_false_recipient_true,
                'key_exchange_complete': self._handle_key_exchange_complete,
            }

            # Determine state and call the appropriate handler
            state = self._determine_key_exchange_state(data)
            print(state)
            if state in state_handlers:
                state_handlers[state](data)
            else:
                emit("error", {"message": "Key exchange failed due to invalid state"})
                raise ValueError("Invalid key exchange state.")

        except ValueError as ve:
            print(f"Validation error during key exchange: {ve}")
            emit("error", {"message": str(ve)})

        except Exception as e:
            print(f"Error in key exchange initialization: {e}")
            emit("error", {"message": "Key exchange initialization failed"})

    def _determine_key_exchange_state(self, data):
        """
        Determine the key exchange state based on the input data.
        """
        if not data.get('recipient_process_secret', True):
            return 'recipient_process_secret_false'
        elif not data.get('sender_process_secret', True) and data.get('recipient_process_secret', False):
            return 'sender_process_secret_false_recipient_true'
        elif data.get("key_exchange_complete", True):
            return 'key_exchange_complete'
        return 'invalid_state'

    def _handle_recipient_process_secret_false(self, data):
        """
        Handle the case where recipient_process_secret is False.
        """
        user = User.query.filter_by(username=data.get('recipient_name')).first()
        if not user:
            raise ValueError("Recipient user not found.")

        session_recipient = Session.query.filter_by(user_id=user.id).first()
        if not session_recipient:
            raise ValueError("Session for recipient user not found.")

        session_id = session.get("session_id")
        sender_socket_id = self.cache_utils.retrieve(f"current_socket_{session_id}")
        recipient_socket_id = session_recipient.socket_id
        self.cache_utils.store(f"current_recipient_socket_{session_id}", recipient_socket_id)

        emit(
            "key_exchange_response_recipient",
            {
                "public_key": data.get('public_key'),
                "sender_socket_id": sender_socket_id,
                "recipient_socket_id": recipient_socket_id,
            },
            to=recipient_socket_id,
        )

    def _handle_sender_process_secret_false_recipient_true(self, data):
        """
        Handle the case where sender_process_secret is False and recipient_process_secret is True.
        """
        session_id = session.get("session_id")
        print(request.sid)
        self.cache_utils.store(f"current_socket_{session_id}", request.sid)
        self.cache_utils.store(f"current_recipient_socket_{session_id}", data.get('sender_socket_id'))

        emit(
            "key_exchange_response_sender",
            {
                "public_key": data.get('public_key'),
                "recipient_socket_id": request.sid,
                "key_exchange_complete": True,

            },
            to=data.get('sender_socket_id'),
        )

    def _handle_key_exchange_complete(self):
        """
        Handle the case where key_exchange_complete is True.
        """
        emit("key_exchange_complete", {"message": "Key exchange complete"})

    def handle_message(self, data):
        """
        Handle the receipt and broadcasting of messages.
        Saves the chat first, then saves the chat recipient after the chat is saved.
        Decrypts incoming messages and re-encrypts them for each recipient.
        """
        try:
            print(data)
            session_id = session.get("session_id")
            print(f"session_id {session_id}")

            # Retrieve socket IDs
            sender_socket_id = self.cache_utils.retrieve(f"current_socket_{session_id}")
            recipient_socket_id = self.cache_utils.retrieve(f"current_recipient_socket_{session_id}")
            recipient_session = Session.query.filter_by(socket_id=recipient_socket_id).first()
            username = self.cache_utils.retrieve(f"current_user_name_{session_id}")
            user_id = self.cache_utils.retrieve(f"current_user_{session_id}")

            if not (recipient_session and user_id):
                emit("error", {"message": "Invalid session or recipient data"})
                return
            try:
                # Save Chat instance
                chat = Chat(
                    user_id=user_id,
                    message_body=data.get('message'),
                    salt=data.get('salt')
                )
                db.session.add(chat)
                db.session.commit()  # Commit to generate a Chat ID
            except Exception as e:
                # Rollback in case of error
                db.session.rollback()
                print(f"Error handling message: {e}")
                emit("error", {"message": "Message handling failed"})
                return

            # Save ChatRecipient instance
            chat_recipient = ChatRecipient(
                recipient_id=recipient_session.user_id,
                recipient_group_id=None,  # Replace with appropriate logic or value
                message_id=chat.id,  # Use the saved chat's ID
                is_read=False
            )
            db.session.add(chat_recipient)
            db.session.commit()

            print(f"recipient_socket_id: {recipient_socket_id}")
            print(f"sender_socket_id {sender_socket_id}")

            if data.get('socket_id_for_another') != sender_socket_id:
                # Emit the message to the recipient
                emit("receive_message",
                     {'message': data.get('message'),
                      'username': username,
                      },
                     to=recipient_socket_id
                     )
            else:
                print("sender just send to himself")
                return
        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            print(f"Error handling message: {e}")
            emit("error", {"message": "Message handling failed"})
            return
