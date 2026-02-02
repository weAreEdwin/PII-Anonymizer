from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "PII Anonymization System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./pii_anonymizer.db"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str = "your-encryption-key-here-change-in-production"
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = "pdf,docx,txt"
    upload_dir: str = "./uploads"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Rate Limiting
    rate_limit_decrypt: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as list"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
