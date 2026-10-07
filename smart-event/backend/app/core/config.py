from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/smart_event"
    TEST_DATABASE_URL: Optional[str] = "sqlite:///./test.db"
    SECRET_KEY: str = "change_this_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    QR_CODE_DIR: str = "qr_codes"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
