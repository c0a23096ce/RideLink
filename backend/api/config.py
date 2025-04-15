from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mapbox_api_key: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"
        extra = "forbid"  # デフォルトだが念のため明示

settings = Settings()

