from pydantic import BaseModel
from typing import Optional


class M2MTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    client_id: Optional[str] = None
    exp: Optional[int] = None
