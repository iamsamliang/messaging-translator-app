from typing import Any, Annotated
from pydantic import (
    model_validator,
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv, load_dotenv
from typing_extensions import Self
from pathlib import Path

load_dotenv(find_dotenv(".env"))


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


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

    # Database
    RDS_HOSTNAME: str
    RDS_PORT: int
    RDS_USERNAME: str
    RDS_PASSWORD: str
    RDS_DB_NAME: str
    DB_QUERY_PARAMS: str

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.RDS_USERNAME,
            password=self.RDS_PASSWORD,
            host=self.RDS_HOSTNAME,
            port=self.RDS_PORT,
            path=self.RDS_DB_NAME,
            query=self.DB_QUERY_PARAMS,
        )

    REDIS_HOST: str
    REDIS_PORT: int

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    # for configuring fastapi-mail to send emails
    MAIL_USERNAME: str
    MAIL_PASSWORD: str  # For GMAIL, enable 2FA and use an App Password
    MAIL_SERVER: str
    MAIL_PORT: int = 587  # Use 465 for SSL. Use TLS bc it's the newer version of SSL
    MAIL_FROM: str
    MAIL_FROM_NAME: str = PROJECT_NAME
    MAIL_STARTTLS: bool = True  # To use TLS. True for port 587
    MAIL_SSL_TLS: bool = False  # To use SSL. False for port 587
    MAIL_TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates" / "email"
    # SMTP server will authenticate using the provided MAIL_USERNAME AND MAIL_PW
    MAIL_USE_CREDENTIALS: bool = True
    # Ensures that the connection is secure and the SMTP server is trusted. Set to True in production
    MAIL_VALIDATE_CERTS: bool = True
    MAIL_DEBUG: bool = False

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.MAIL_FROM_NAME:
            self.MAIL_FROM_NAME = self.PROJECT_NAME
        return self

    ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS: int
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int

    UNVERIFIED_USERS_DBCLEANUP_SECS: int = 60 * 60 * 24  # 24 hours

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()  # type: ignore
# (pydantic finds the arguments)
