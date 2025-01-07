from flask_cyber_app.utils.cache_utils import CacheUtils
from flask_cyber_app.utils.security_utils import SecurityUtils


class ChannelManager:
    def __init__(self):
        self.cache_utils = CacheUtils  # Use CacheUtils for storing shared secrets

    def establish_shared_secret(self, sender_socket_id, recipient_socket_id, sender_public_key, recipient_private_key, ttl=300):
        """
        Derive and store a shared secret between two users.
        """
        # Derive the shared secret using sender's public key and recipient's private key
        shared_secret = SecurityUtils.derive_shared_secret(
            recipient_private_key,
            SecurityUtils.deserialize_public_key(sender_public_key.encode())
        )

        # Derive Fernet key from the shared secret
        fernet_key = SecurityUtils.derive_fernet_key(shared_secret).decode()

        # Generate cache keys for both sender-recipient and recipient-sender (bidirectional)
        key1 = f"{sender_socket_id}:{recipient_socket_id}"
        key2 = f"{recipient_socket_id}:{sender_socket_id}"

        # Store in cache with TTL
        self.cache_utils.store(key1, fernet_key, ttl)
        self.cache_utils.store(key2, fernet_key, ttl)
        return fernet_key

    def get_fernet_instance(self, sender_socket_id, recipient_socket_id):
        """
        Retrieve the Fernet instance for the shared secret.
        """
        # Retrieve the shared secret from the cache
        cache_key = f"{sender_socket_id}:{recipient_socket_id}"
        fernet_key = self.cache_utils.retrieve(cache_key)
        if not fernet_key:
            raise ValueError(f"No shared secret found for {sender_socket_id} and {recipient_socket_id}")
        return SecurityUtils.create_fernet_instance(fernet_key.encode())

    def encrypt_message(self, sender_socket_id, recipient_socket_id, message):
        """
        Encrypt a message for a recipient using the shared secret.
        """
        fernet = self.get_fernet_instance(sender_socket_id, recipient_socket_id)
        return fernet.encrypt(message.encode()).decode()

    def decrypt_message(self, sender_socket_id, recipient_socket_id, encrypted_message):
        """
        Decrypt a message from a sender using the shared secret.
        """
        fernet = self.get_fernet_instance(sender_socket_id, recipient_socket_id)
        return fernet.decrypt(encrypted_message.encode()).decode()

    def cleanup_expired_keys(self):
        """
        Optionally remove expired keys. Not necessary if CacheUtils handles it automatically.
        """
        # CacheUtils already removes expired items, so this might not be needed.
        pass
