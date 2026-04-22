import secrets
from typing import Annotated
from pydantic import UrlConstraints, Field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )

    # JWT Token Config
    SECRET_KEY: str = Field(secrets.token_urlsafe(32), repr=False)
    SIGN_ALGORITHM: str =  Field("HS256", repr=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MongoDB Client
    MONGO_DSN: Annotated[
        MultiHostUrl,
        UrlConstraints(allowed_schemes=['mongodb', 'mongodb+srv']),
    ] = Field(MultiHostUrl('mongodb://localhost/'), repr=False)

settings = Settings()