from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "dummy_key"
    # Use SQLite for local development in this environment since Postgres is not available
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
