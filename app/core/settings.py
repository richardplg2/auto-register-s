from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT, description="Application environment"
    )

    # Auto register configuration
    AUTO_REGISTER_MAX_SESSIONS: int = Field(
        default=1000, description="Maximum number of camera sessions"
    )
    AUTO_REGISTER_HEARTBEAT_INTERVAL: int = Field(
        default=30, description="Heartbeat interval in seconds"
    )

    AUTO_REGISTER_SERVER_PORT: int = Field(
        default=9600, description="Server port for auto registration"
    )

    AUTO_REGISTER_SERVER_HOST: str = Field(
        default="0.0.0.0", description="Server host for auto registration"
    )

    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=20, description="Redis connection pool size")
    REDIS_STREAM_NAME: str = Field(
        default="camera_events", description="Redis stream name for events"
    )
    REDIS_STREAM_MAX_LEN: int = Field(
        default=10000, description="Maximum stream length"
    )

    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Service configuration
    SERVICE_NAME: str = Field(
        default="auto-register-service", description="Service name"
    )
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    SERVICE_HOST: str = Field(default="0.0.0.0", description="Service host")
    SERVICE_PORT: int = Field(default=8001, description="Service port")

    # Database configuration
    DATABASE_HOST: str = Field(default="localhost", description="Database host")
    DATABASE_PORT: int = Field(default=5432, description="Database port")
    DATABASE_USER: str = Field(default="user", description="Database user")
    DATABASE_PASSWORD: str = Field(default="password", description="Database password")
    DATABASE_SCHEMA: str = Field(default="dbname", description="Database schema")

    AWS_ACCESS_KEY_ID: str = Field(
        default="your_access_key_id", description="AWS access key ID"
    )
    AWS_SECRET_ACCESS_KEY: str = Field(
        default="your_secret_access_key", description="AWS secret access key"
    )
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_S3_BUCKET: str = Field(default="your_s3_bucket", description="S3 bucket name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
        extra="ignore",
    )

    def is_development(self) -> bool:
        return self.ENVIRONMENT == EnvironmentType.DEVELOPMENT

    def is_production(self) -> bool:
        return self.ENVIRONMENT == EnvironmentType.PRODUCTION

    def is_staging(self) -> bool:
        return self.ENVIRONMENT == EnvironmentType.STAGING

    def get_db_url(self) -> str:
        return f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_SCHEMA}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
