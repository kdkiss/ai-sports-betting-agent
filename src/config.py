from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    SPORTSDB_API_KEY: str = os.getenv("SPORTSDB_API_KEY", "1")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # LLM Settings
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TEMPERATURE: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7"))
    DEEPSEEK_MAX_TOKENS: int = int(os.getenv("DEEPSEEK_MAX_TOKENS", "1000"))
    DEEPSEEK_TOP_P: float = float(os.getenv("DEEPSEEK_TOP_P", "0.95"))
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "sports_ai_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Application
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

    # API Rate Limits
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))
    API_RATE_WINDOW: int = int(os.getenv("API_RATE_WINDOW", "60"))

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Webhook
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")

    # Cache TTL
    CACHE_TTL_MATCH: int = int(os.getenv("CACHE_TTL_MATCH", "300"))
    CACHE_TTL_TEAM: int = int(os.getenv("CACHE_TTL_TEAM", "3600"))
    CACHE_TTL_USER: int = int(os.getenv("CACHE_TTL_USER", "86400"))
    CACHE_TTL_API: int = int(os.getenv("CACHE_TTL_API", "900"))

    # Image Processing
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    # API Base URLs
    SPORTSDB_BASE_URL: str = "https://www.thesportsdb.com/api/v1/json"

    @classmethod
    def get_database_url(cls) -> str:
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"

    @classmethod
    def get_redis_url(cls) -> str:
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/0"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/0"

    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith("_") and isinstance(value, (str, int, bool, float))
        } 