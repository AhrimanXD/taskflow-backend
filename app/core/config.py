from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_URL = Path(__file__).parent.parent.parent.resolve()



class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # CORS. Both are overridable on the host (e.g.
    # `fastapi cloud env set CORS_ORIGINS`) without a code change.
    # CORS_ORIGINS: exact allowed origins (comma-separated) — used for localhost.
    CORS_ORIGINS: str = "http://localhost:3000"
    # CORS_ORIGIN_REGEX: matches the deployed Vercel frontend — the production
    # alias AND every per-deploy preview URL (taskflow-frontend-<hash>.vercel.app).
    CORS_ORIGIN_REGEX: str = r"https://taskflow-frontend-[\w-]+\.vercel\.app"
    model_config = SettingsConfigDict(env_file=BASE_URL/'.env', env_file_encoding='utf-8')

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        return self.CORS_ORIGIN_REGEX.strip() or None
    
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

