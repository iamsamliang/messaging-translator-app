from pydantic import BaseModel


class TokenPayLoad(BaseModel):
    username: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str
