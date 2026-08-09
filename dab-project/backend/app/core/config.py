import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DISCORD_PRIMARY_TOKEN: str = os.getenv("DISCORD_PRIMARY_TOKEN", "your-primary-bot-token")
    DISCORD_AUX_TOKENS: str = os.getenv("DISCORD_AUX_TOKENS", "aux-token-1,aux-token-2,aux-token-3,aux-token-4")
    DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "your-client-id")
    DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "your-client-secret")
    DISCORD_REDIRECT_URI: str = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/oauth/callback")
    
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "dab_database")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-jwt-and-sessions")

    class Config:
        env_file = ".env"

settings = Settings()
