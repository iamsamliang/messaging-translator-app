from pydantic import BaseModel


class TokenPayLoad(BaseModel):
    username: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str
