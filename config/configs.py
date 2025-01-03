import secrets
from decouple import config

import secrets
from decouple import config


class Config:
    DB_CONFIG = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'your_secret_key',
    }
