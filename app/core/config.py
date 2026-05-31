import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    POLICY_DATA_PATH: str = os.getenv("POLICY_DATA_PATH", "data/policy_terms.json")

    class Config:
        env_file = ".env"

settings = Settings()
