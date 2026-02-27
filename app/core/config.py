from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_URL = Path(__file__).parent.parent.parent.resolve()



class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = "" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    model_config = SettingsConfigDict(env_file=BASE_URL/'.env', env_file_encoding='utf-8')
    
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

