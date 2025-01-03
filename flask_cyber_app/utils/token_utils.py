import jwt
import datetime

from config.configs import Config


class TokenUtils:
    SECRET_KEY = Config.CONFIG['SECRET_KEY']
    REFRESH_SECRET_KEY = Config.CONFIG['REFRESH_SECRET_KEY']

    @staticmethod
    def generate_access_token(user_id, expire_minutes=15):
        """Generate a short-lived access token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes),
        }
        return jwt.encode(payload, TokenUtils.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def generate_refresh_token(user_id, expire_days=7):
        """Generate a long-lived refresh token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=expire_days),
        }
        return jwt.encode(payload, TokenUtils.REFRESH_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_access_token(token):
        """Decode and validate the access token."""
        try:
            return jwt.decode(token, TokenUtils.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Access token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid access token")

    @staticmethod
    def decode_refresh_token(token):
        """Decode and validate the refresh token."""
        try:
            return jwt.decode(token, TokenUtils.REFRESH_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")
