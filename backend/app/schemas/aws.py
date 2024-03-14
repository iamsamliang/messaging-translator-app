from typing import Annotated
from pydantic import BaseModel, field_validator, StringConstraints


class S3PreSignedURLPOSTResponse(BaseModel):
    url: str
    fields: dict[str, str]


class S3PreSignedURLPOSTRequest(BaseModel):
    filename: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
    convo_id: int | None = None
    about: Annotated[str, StringConstraints(strip_whitespace=True)]

    @field_validator("filename", mode="after")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename")
        return v


class S3PreSignedURLGETRequest(BaseModel):
    user_ids: list[int] | None = None
    convo_id: int | None = None
