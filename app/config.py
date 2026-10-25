from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "827e4bab9fa724379a6571e23229f2ffa007f63ec8480adead6be1cfabb00a0a"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./notes.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()