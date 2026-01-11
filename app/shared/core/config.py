from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    PROJECT_NAME: str
    SECRET_KEY: str
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Model Configuration
    AI_REASONING_MODEL: str = "llama3.2"
    AI_SENTIMENT_MODEL: str = "finbert"  # finbert | openai | ensemble
    AI_REASONING_PROVIDER: str = "ollama"  # ollama | openai | gemini

    # AI API Keys (optional - only for cloud providers)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Binance API Configuration
    BINANCE_API_BASE_URL: str
    BINANCE_WS_BASE_URL: str
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None

    # MongoDB Configuration for News Module
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "trading_controller"
    NEWS_COLLECTION: str = "news_articles"
    INSIGHTS_COLLECTION: str = "news_insights"

    # LLM Configuration for News Parsing
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama2"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # News Crawler Configuration
    NEWS_CRAWL_INTERVAL_MINUTES: int = 60
    NEWS_SOURCES: List[str] = ["coindesk", "reuters", "bloomberg", "twitter"]
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ALGORITHM: str = "HS256"


# Settings can be instantiated without arguments because BaseSettings
# loads all required fields from environment variables
settings = Settings()  # pyright: ignore[reportCallIssue]

