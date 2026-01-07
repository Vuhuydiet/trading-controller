from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    PROJECT_NAME: str
    SECRET_KEY: str
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Binance API Configuration
    BINANCE_API_BASE_URL: str
    BINANCE_WS_BASE_URL: str
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    ALGORITHM: str = "HS256"

settings = Settings()
