import random
from flask import request, g
from flask_socketio import emit
from flask_cyber_app.models.models import db, User, Chat, Session
from flask_cyber_app.utils.security_utils import SecurityUtils


class ChatController:
    def __init__(self, socketio):
        self.socketio = socketio
        self.register_events()
        self.events_registered = False

    def register_events(self):
        self.socketio.on_event("key_exchange_init", self.handle_key_exchange_init)
        self.socketio.on_event("key_exchange_final", self.handle_key_exchange_final)
        self.socketio.on_event("send_message", self.handle_message)
        self.socketio.on_event("disconnect", self.handle_disconnect)
        self.events_registered = True

    def handle_key_exchange_init(self):
        # Generate ECDH key pair
        private_key, public_key = SecurityUtils.generate_ecdh_key_pair()

        # Serialize server public key
        server_public_key = SecurityUtils.serialize_public_key(public_key)

        # Temporarily store the private key
        request.sid_private_key = private_key

        # Send server's public key to the client
        emit("key_exchange_response", {"public_key": server_public_key})

    def handle_key_exchange_final(self, data):
        # Deserialize client's public key
        client_public_key = SecurityUtils.deserialize_public_key(data["public_key"].encode())

        # Retrieve server's private key
        private_key = getattr(request, "sid_private_key", None)
        if not private_key:
            emit("error", {"message": "Private key not found for this session"})
            return

        # Derive the shared secret and Fernet key
        shared_secret = SecurityUtils.derive_shared_secret(private_key, client_public_key)
        fernet_key = SecurityUtils.derive_fernet_key(shared_secret).decode()

        # Fetch or create a user
        username = f"User_{random.randint(1000, 9999)}"
        avatar_url = f"https://avatar.iran.liara.run/public/boy?username={username}"
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(avatar=avatar_url)
            print(user)
            db.session.add(user)
            db.session.commit()

        # Store session in the database
        session = Session(socket_id=request.sid, user_id=user.id, fernet_key=fernet_key)
        print(session)
        db.session.add(session)
        db.session.commit()

        emit("key_exchange_complete", {"message": "Key exchange successful!"})

    def handle_message(self, data):
        # Retrieve session from the global context
        session = getattr(g, "current_session", None)
        if not session:
            emit("error", {"message": "Active session not found!"})
            return

        fernet = SecurityUtils.create_fernet_instance(session.fernet_key.encode())

        # Decrypt incoming message
        decrypted_message = fernet.decrypt(data["message"].encode()).decode()
        print(f"Decrypted message from client: {decrypted_message}")

        # Save chat message to database
        chat_message = Chat(user_id=session.user_id, message=decrypted_message)
        db.session.add(chat_message)
        db.session.commit()

        # Encrypt and broadcast the response
        encrypted_response = fernet.encrypt(f"Server received: {decrypted_message}".encode())
        emit("new_message", {"message": encrypted_response.decode()}, broadcast=True)

    def handle_disconnect(self):
        # Remove session from the database
        session = Session.query.filter_by(socket_id=request.sid).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            print(f"Session for socket {request.sid} has been deleted.")
