from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
from typing import Dict, Any
from ..config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        # Use the secret key from settings as the encryption key base
        self.key = self._derive_key(settings.secret_key)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            # Use a fixed salt derived from the password for consistency
            # In production, use a proper key management system
            salt = password[:16].encode().ljust(16, b'0')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt text and return base64 encoded string"""
        if not text:
            return ""
        
        encrypted_data = self.cipher.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt base64 encoded encrypted text"""
        if not encrypted_text:
            return ""
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary as JSON and return base64 encoded string"""
        json_str = json.dumps(data)
        return self.encrypt_text(json_str)
    
    def decrypt_dict(self, encrypted_json: str) -> Dict[str, Any]:
        """Decrypt base64 encoded JSON back to dictionary"""
        json_str = self.decrypt_text(encrypted_json)
        return json.loads(json_str)
    
    def encrypt_with_password(self, text: str, password: str) -> str:
        """Encrypt text with a user-provided password"""
        # Derive key from user password
        user_key = self._derive_key(password)
        user_cipher = Fernet(user_key)
        
        encrypted_data = user_cipher.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_with_password(self, encrypted_text: str, password: str) -> str:
        """Decrypt text with a user-provided password"""
        try:
            # Derive key from user password
            user_key = self._derive_key(password)
            user_cipher = Fernet(user_key)
            
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = user_cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError("Incorrect password or corrupted data")


# Global instance
encryption_service = EncryptionService()
