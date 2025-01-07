import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization


class SecurityUtils:
    @staticmethod
    def generate_ecdh_key_pair():
        """Generate an ECDH key pair."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def serialize_public_key(public_key):
        """Serialize a public key to PEM format."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    @staticmethod
    def deserialize_public_key(public_key_bytes):
        """Deserialize a PEM-formatted public key."""
        return serialization.load_pem_public_key(public_key_bytes)

    @staticmethod
    def derive_shared_secret(private_key, peer_public_key):
        """Derive a shared secret using ECDH."""
        shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
        # Convert shared secret to base64 for logging
        shared_secret_base64 = base64.urlsafe_b64encode(shared_secret).decode('utf-8')
        print("Shared Secret (Base64):", shared_secret_base64)
        return shared_secret

    @staticmethod
    def derive_fernet_key(shared_secret):
        """Derive a Fernet-compatible symmetric key from a shared secret."""
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"handshake data"
        ).derive(shared_secret)
        return base64.urlsafe_b64encode(derived_key)

    @staticmethod
    def create_fernet_instance(fernet_key):
        """Create a Fernet instance using the given key."""
        return Fernet(fernet_key)
