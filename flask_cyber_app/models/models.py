from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.sql import func
from config.extensions import Extension

db = Extension.db


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(500))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    chats = db.relationship('Chat', back_populates='user', cascade='all, delete-orphan')

    user_groups = db.relationship('UserGroup', back_populates='user')


class Chat(db.Model):
    __tablename__ = "chats"
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    subject = db.Column(db.String(100), nullable=True)  # Subject (max 100 characters)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"),
                        nullable=False)  # Foreign key to User table
    message_body = db.Column(db.Text, nullable=False)  # Message body as CLOB
    salt = db.Column(db.String(32), nullable=False)  # Salt used for encryption
    create_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation date
    parent_message_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=True)  # Self-referential FK
    expiry_date = db.Column(db.DateTime, nullable=True)  # Expiry date
    is_reminder = db.Column(db.Boolean, default=False, nullable=True)  # Is it a reminder
    next_remind_date = db.Column(db.DateTime, nullable=True)  # Next reminder date
    reminder_frequency_id = db.Column(db.Integer, nullable=True)  # Frequency ID (could link to another table)

    # Relationships
    # Corrected back-populates reference
    user = db.relationship('User', back_populates='chats')
    parent_message = db.relationship('Chat', remote_side=[id])  # Self-referential relationship
    recipients = db.relationship('ChatRecipient', backref='chats', lazy=True)  # Relationship to recipients

    def __repr__(self):
        return f"<Message {self.id}: {self.subject}>"


class ChatRecipient(db.Model):
    __tablename__ = 'chat_recipients'
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                             nullable=True)  # Recipient (foreign key to User table)
    recipient_group_id = db.Column(db.Integer, nullable=True)  # Recipient group (if applicable)
    message_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)  # FK to Message table
    is_read = db.Column(db.Boolean, default=False, nullable=False)  # Has the message been read

    def __repr__(self):
        return f"<ChatRecipient {self.id}: Recipient {self.recipient_id}, Message {self.message_id}>"


# Group model
class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.String(1), nullable=False, default='Y')

    # Relationships
    group_users = db.relationship('UserGroup', back_populates='group')


# UserGroup model (association table)
class UserGroup(db.Model):
    __tablename__ = 'user_groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    create_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.String(1), nullable=False, default='Y')

    # Relationships
    user = db.relationship('User', back_populates='user_groups')
    group = db.relationship('Group', back_populates='group_users')


class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True)
    socket_id = db.Column(db.String(255), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
