import secrets
from typing import Annotated
from pydantic import UrlConstraints, Field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra="ignore"
    )

    # JWT Token Config
    SECRET_KEY: str 
    SIGN_ALGORITHM: str =  Field("HS256", repr=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 10
    
    # MongoDB Client
    MONGO_DSN: Annotated[
        MultiHostUrl,
        UrlConstraints(allowed_schemes=['mongodb', 'mongodb+srv']),
    ] = Field(MultiHostUrl('mongodb://localhost/'), repr=False)

@lru_cache
def get_settings():
    return Settings() # type: ignore