from pydantic import BaseModel
from datetime import datetime


class TokenPayLoad(BaseModel):
    userid: str
    iat: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class VerificationPayLoad(BaseModel):
    token: str
