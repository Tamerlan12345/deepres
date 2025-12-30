from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "dummy_key"
    # Use SQLite for local development in this environment since Postgres is not available
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()
