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