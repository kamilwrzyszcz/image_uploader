import base64
import zlib
import pickle
from typing import Any
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_data(data: Any) -> bytes:
    """Encrypt data with Fernet symmetric key algorithm."""
    key = base64.urlsafe_b64encode(bytes(settings.SECRET_KEY, 'utf-8'))
    fernet = Fernet(key)

    encoded_data = zlib.compress(pickle.dumps(data, 0)) 

    return fernet.encrypt(encoded_data)

def decrypt_data(encMessage: bytes) -> Any:
    """Decrypt data. Inverse of the above function."""
    key = base64.urlsafe_b64encode(bytes(settings.SECRET_KEY, 'utf-8'))
    fernet = Fernet(key)

    decMessage = fernet.decrypt(bytes(encMessage, 'utf-8'))
    
    return pickle.loads(zlib.decompress(decMessage))
