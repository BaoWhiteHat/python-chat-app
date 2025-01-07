import base64
import random
import time
from flask import session as flask_session
from flask import request
from flask_socketio import emit
from flask_cyber_app.models.models import Session, db
from flask_cyber_app.socket_connection.channel_manager import ChannelManager
from flask_cyber_app.utils.cache_utils import CacheUtils
from flask_cyber_app.utils.security_utils import SecurityUtils


class ChatController:
    def __init__(self, socketio):
        self.socketio = socketio
        self.channel_manager = ChannelManager()  # Initialize the ChannelManager
        self.register_events()
        self.events_registered = False

    def register_events(self):
        self.socketio.on_event("key_exchange_init", self.handle_key_exchange_init)
        print("key_exchange_init")
        self.socketio.on_event("key_exchange_final", self.handle_key_exchange_final)
        print("key_exchange_final")
        self.socketio.on_event("send_message", self.handle_message)
        print("send_message")

    def handle_key_exchange_init(self):
        """
        Handle the initialization of key exchange.
        Generates and sends the server's public key to the client.
        """
        try:
            # Generate ECDH key pair
            private_key, public_key = SecurityUtils.generate_ecdh_key_pair()

            # Serialize server public key
            server_public_key = SecurityUtils.serialize_public_key(public_key)

            # Remove PEM headers, footers, and line breaks
            server_public_key_base64 = "".join(
                server_public_key.splitlines()[1:-1]  # Strip headers and footers
            )

            # Temporarily store the private key in the cache
            CacheUtils.store(f"private_key_{request.sid}", private_key)

            # Send server's public key to the client
            emit("key_exchange_response", {"public_key": server_public_key})
        except Exception as e:
            print(f"Error in key exchange initialization: {e}")
            emit("error", {"message": "Key exchange initialization failed"})

    def handle_key_exchange_final(self, data):
        """
        Finalize the key exchange and derive shared secrets for encryption.
        """
        try:
            print("handle_key_exchange_final function call")

            # Deserialize the client's public key
            client_public_key_bytes = f"-----BEGIN PUBLIC KEY-----\n{data['public_key']}\n-----END PUBLIC KEY-----"
            client_public_key = SecurityUtils.deserialize_public_key(client_public_key_bytes.encode())

            # Retrieve server's private key from the cache
            private_key = CacheUtils.retrieve(f"private_key_{request.sid}")
            if not private_key:
                emit("error", {"message": "Key exchange failed: private key not found"})
                return

            # Derive a shared secret using ECDH
            shared_secret = SecurityUtils.derive_shared_secret(private_key, client_public_key)
            shared_secret_base64 = base64.urlsafe_b64encode(shared_secret).decode('utf-8')
            print(f"shared_secret: {shared_secret_base64}")

            # Derive a Fernet-compatible symmetric key
            fernet_key = SecurityUtils.derive_fernet_key(shared_secret)
            CacheUtils.store(f"fernet_key{request.sid}", fernet_key)
            print(fernet_key)

            # Save the derived Fernet key and socket ID to the session model
            session = Session.query.filter_by(user_id=flask_session.get("current_user")).first()
            # available
            if session:
                session.fernet_key = fernet_key.decode()
                session.socket_id = request.sid
                db.session.commit()
                print(f"Session updated: User ID {session.user_id}, Socket ID {session.socket_id}, Fernet Key saved.")

            emit("key_exchange_complete", {"message": "Key exchange successful!"})
        except Exception as e:
            print(f"Error in handle_key_exchange_final: {e}")
            emit("error", {"message": "Key exchange failed"})

    def handle_message(self, data):
        """
        Handle the receipt and broadcasting of messages.
        Decrypts incoming messages and re-encrypts them for each recipient.
        """
        try:
            print("handle_message function call")
            print(data['message'])

            # Find the sender's session using the socket ID
            sender_session = Session.query.filter_by(socket_id=request.sid).first()
            if not sender_session:
                print("can not find sender_session")
                emit("error", {"message": "Sender session not found"})
                return
            print("handle_message function call 1")
            # Retrieve the sender's Fernet key
            sender_fernet_key = sender_session.fernet_key
            if not sender_fernet_key:
                emit("error", {"message": "Sender Fernet key not found"})
                return
            print("handle_message function call 2")
            # Decrypt the incoming message using the sender's Fernet key
            sender_fernet = SecurityUtils.create_fernet_instance(sender_fernet_key.encode())
            print(sender_fernet)
            decrypted_message = sender_fernet.decrypt(data["message"].encode(), ttl=3600).decode()

            print(f"Decrypted message from sender: {decrypted_message}")

            # Encrypt and send the message to all recipients
            all_sessions = Session.query.filter(Session.expire_at > time.time()).all()
            for recipient_session in all_sessions:
                # Retrieve the recipient's Fernet key
                recipient_fernet_key = recipient_session.fernet_key
                if not recipient_fernet_key:
                    print(f"Fernet key not found for recipient {recipient_session.user_id}")
                    continue

                # Encrypt the message for the recipient
                recipient_fernet = SecurityUtils.create_fernet_instance(recipient_fernet_key.encode())
                encrypted_message = recipient_fernet.encrypt(decrypted_message.encode()).decode()

                # Emit the encrypted message to the recipient
                emit(
                    "new_message",
                    {
                        "message": encrypted_message,
                        "username": sender_session.user.username
                    },
                    room=recipient_session.socket_id,
                )
                print(f"Message sent to {recipient_session.socket_id} (User ID: {recipient_session.user_id})")

        except Exception as e:
            print(f"Error handling message: {e}")
            emit("error", {"message": "Message handling failed"})

