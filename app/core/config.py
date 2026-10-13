from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Decaigny API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database Settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # CORS Settings
    BACKEND_CORS_ORIGINS: str = ""

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # Your Daily Drive (YDD) ERP Settings
    YDD_BASE_URL: str = "https://api.yourdailydrive.com"
    YDD_DEALER_ID: str = ""
    YDD_API_KEY: str = ""
    YDD_LANGUAGE: str = "nl"
    YDD_TIMEOUT_SECONDS: int = 30

    # Claude AI (Anthropic) Settings
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    ANTHROPIC_MAX_TOKENS: int = 1024
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_TIMEOUT_SECONDS: int = 60
    ANTHROPIC_MAX_RETRIES: int = 1

    # AI post generation
    AI_DEFAULT_LANGUAGE: str = "nl"
    AI_MAX_VALIDATION_RETRIES: int = 1
    AI_PENDING_MAX_AGE_DAYS: int = 7
    AI_PENDING_BATCH_LIMIT: int = 10
    AI_MAX_FAILURES_PER_VEHICLE: int = 6

    model_config = SettingsConfigDict(
        case_sensitive=True,
        # env_file=".env"
        env_file=str(BASE_DIR / ".env")
    )

    @property
    def cors_origins(self) -> List[str]:
        """Get the CORS origins as a list."""
        origins = [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        # For development, ensure we have both http and https variants
        all_origins = []
        for origin in origins:
            all_origins.append(origin)
            if origin.startswith('http://'):
                all_origins.append(origin.replace('http://', 'https://'))
        return all_origins

settings = Settings() 