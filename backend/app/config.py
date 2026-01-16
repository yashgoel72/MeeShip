from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # JWT Settings
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email Settings (SendGrid)
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@meesho-optimizer.com"

    # Rate Limiting
    RATE_LIMIT_ATTEMPTS: int = 3
    RATE_LIMIT_WINDOW_MINUTES: int = 5

    # Azure Storage (optional)
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: Optional[str] = None
    AZURE_STORAGE_PUBLIC_BASE_URL: Optional[str] = None

    # S3 Storage (Backblaze B2 or compatible)
    S3_ENABLED: bool = True
    S3_ENDPOINT: str = "https://s3.us-east-005.backblazeb2.com"
    S3_ACCESS_KEY: str = "your_keyID"
    S3_SECRET_KEY: str = "your_app_key"
    S3_BUCKET: str = "meeship-images"
    S3_PRESIGNED_URL_EXPIRY: int = 900  # 15 minutes in seconds

    # Azure Foundry (FLUX) integration
    AZURE_FOUNDRY_ENDPOINT: Optional[str] = None
    AZURE_FOUNDRY_MODEL_NAME: Optional[str] = "FLUX.1-Kontext-pro"
    AZURE_FOUNDRY_API_KEY: Optional[str] = None
    # Feature flag to enable/disable using Azure Foundry per deployment
    USE_AZURE_FOUNDRY: bool = False

    # Azure OpenAI (gpt-image-1.5) integration
    # If not set, the code falls back to AZURE_FOUNDRY_* values.
    AZURE_OPENAI_ENDPOINT: Optional[str] = ""
    AZURE_OPENAI_API_KEY: Optional[str] = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = ""
    OPENAI_API_VERSION: str = ""

    # Razorpay Configuration
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Kinde Authentication
    KINDE_DOMAIN: str = ""  # e.g., https://yourbusiness.kinde.com
    KINDE_CLIENT_ID: str = ""
    KINDE_CLIENT_SECRET: str = ""
    KINDE_REDIRECT_URI: str = ""  # e.g., http://localhost:3000/api/auth/kinde/callback
    KINDE_LOGOUT_REDIRECT_URI: str = ""  # e.g., http://localhost:3000

    # Application Settings
    APP_NAME: str = "Meesho Image Optimizer"
    DEBUG: bool = False

    # For backwards compatibility
    @property
    def secret_key(self) -> str:
        return self.JWT_SECRET_KEY
    
    @property
    def algorithm(self) -> str:
        return self.JWT_ALGORITHM
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def refresh_token_expire_days(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = Settings()