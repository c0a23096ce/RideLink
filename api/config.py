# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mapbox_api_key: str

    class Config:
        env_file = ".env"  # .envから読み込む

settings = Settings()
