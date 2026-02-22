from pydantic_settings import BaseSettings
from pydantic import Field
import os
import secrets
import sys

def get_default_secret_key():
    print("WARNING: SECRET_KEY not set in environment or .env file. Using a temporary random key. Sessions will not persist on restart.", file=sys.stderr)
    return secrets.token_hex(32)

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "dummy_key"
    # Use SQLite for local development in this environment since Postgres is not available
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    RESET_DB: bool = False

    # Security
    SECRET_KEY: str = Field(default_factory=get_default_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
