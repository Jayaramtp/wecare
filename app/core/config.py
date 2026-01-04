"""
Application configuration settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field, Field
from typing import List, Union
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Project settings
    PROJECT_NAME: str = "Authentication Microservice"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings - stored as string, converted to list via computed field
    allowed_origins_str: str = Field(default="*", validation_alias="ALLOWED_ORIGINS")
    
    @field_validator("allowed_origins_str", mode="before")
    @classmethod
    def parse_allowed_origins_str(cls, v):
        """Accept string or list, convert to string"""
        if isinstance(v, list):
            return ",".join(v)
        return str(v) if v is not None else "*"
    
    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """
        Parse ALLOWED_ORIGINS from string (comma-separated) or return list.
        Handles both comma-separated strings from .env and list values.
        """
        if not self.allowed_origins_str:
            return ["*"]
        
        # Handle comma-separated string
        if self.allowed_origins_str.strip() == "*":
            return ["*"]
        # Split by comma and strip whitespace
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "wecare"
    DB_CHARSET: str = "utf8mb4"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production-use-env-variable"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Argon2 password hashing settings
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536  # 64 MB in KB
    ARGON2_PARALLELISM: int = 4


# Create settings instance
settings = Settings()

