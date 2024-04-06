from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv, load_dotenv
from typing_extensions import Self
from pathlib import Path

load_dotenv(find_dotenv(".env"))


class Settings(BaseSettings):
    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # AWS S3
    S3_PRESIGNED_URL_GET_EXPIRE_SECS: int = 43200  # seconds = 12 hrs
    S3_PRESIGNED_URL_POST_EXPIRE_SECS: int = 1800  # seconds = 30 minutes
    S3_BUCKET_NAME: str

    # DB Items Fetching Limits
    INITIAL_CONVERSATION_LOAD_LIMIT: int
    CHAT_HISTORY_NUM_PREV_MSGS: int

    PROJECT_NAME: str = "SpeakeAIsy"

    FRONTEND_HOST: str

    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    # for configuring fastapi-mail to send emails
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_FROM: str
    MAIL_FROM_NAME: str = PROJECT_NAME
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates" / "email"
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.MAIL_FROM_NAME:
            self.MAIL_FROM_NAME = self.PROJECT_NAME
        return self

    ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS: int
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int

    UNVERIFIED_USERS_DBCLEANUP_SECS: int = 60 * 60 * 24  # 24 hours

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
# (pydantic finds the arguments)
