from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/smart_event"
    TEST_DATABASE_URL: Optional[str] = "sqlite:///./test.db"
    SECRET_KEY: str = "change_this_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    QR_CODE_DIR: str = "qr_codes"
    
    # Phase 3: Payment Configuration
    PAYMENT_PROVIDER: str = "simulation"
    PAYMENT_SIMULATION_ENABLED: bool = True
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_SUCCESS_URL: Optional[str] = "http://localhost:8000/payments/success"
    STRIPE_CANCEL_URL: Optional[str] = "http://localhost:8000/payments/cancel"
    
    # Phase 4: AI & Real-time Configuration
    AI_PROVIDER: str = "fallback"  # Options: fallback, mock, openai, gemini
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gemini-1.5-flash"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
