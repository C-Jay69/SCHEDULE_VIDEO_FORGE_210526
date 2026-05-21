from cryptography.fernet import Fernet
from ..config import settings
import base64
import hashlib


def _get_fernet() -> Fernet:
    # Derive a 32-byte key from the secret_key
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_token(token: str) -> str:
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted_token.encode()).decode()
