from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from ..auth.schemas import M2MTokenRequest, TokenResponse
from ...core.security import verify_m2m_credentials, create_access_token
from ...core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=TokenResponse)
async def get_m2m_token(token_request: M2MTokenRequest):
    """Machine-to-machine token endpoint"""
    if not verify_m2m_credentials(token_request.client_id, token_request.client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": token_request.client_id, "client_id": token_request.client_id},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}
