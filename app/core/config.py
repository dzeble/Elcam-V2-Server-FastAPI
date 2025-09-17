from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "New Elcam API"
    debug: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # M2M Auth
    m2m_client_id: str = "default-client"
    m2m_client_secret: str = "default-secret"
    
    class Config:
        env_file = ".env"


settings = Settings()