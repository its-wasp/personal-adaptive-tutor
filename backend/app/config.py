from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database — either a full DATABASE_URL (for cloud deploys like Neon)
    # or individual parts (for Docker Compose local dev). The full URL
    # takes precedence when set.
    DATABASE_URL: str | None = None
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: str = "5432"

    # LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    LLM_PROVIDER: str = "groq"

    # Search (optional — SearXNG isn't available in cloud deploys)
    SEARXNG_URL: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440  # 24 hours

    # CORS — comma-separated origins for production deploys
    CORS_ORIGINS: str = ""

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")


settings = Settings()
