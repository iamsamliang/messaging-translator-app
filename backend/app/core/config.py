import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".env"))


class Settings(BaseSettings):
    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str = "SpeakeAIsy"
    DATABASE_URL: str
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
# (pydantic finds the arguments)
