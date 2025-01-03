import secrets
from decouple import config


class Config:
    CONFIG = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': secrets.token_hex(32),
        'SESSION_COOKIE_SECURE': True,  # HTTPS-only cookies
        'SESSION_COOKIE_HTTPONLY': True,  # JavaScript cannot access cookies
        'SESSION_COOKIE_SAMESITE': 'Lax',  # Prevent CSRF attacks
    }
