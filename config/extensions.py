from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


class Extension:
    socketio = SocketIO()
    db = SQLAlchemy()
    login_manager = LoginManager()
