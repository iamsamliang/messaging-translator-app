from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".env"))


class Settings(BaseSettings):
    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    S3_PRESIGNED_URL_GET_EXPIRE_SECS: int = 43200  # seconds = 12 hrs
    S3_PRESIGNED_URL_POST_EXPIRE_SECS: int = 1800  # seconds = 30 minutes
    PROJECT_NAME: str = "SpeakeAIsy"
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
# (pydantic finds the arguments)
