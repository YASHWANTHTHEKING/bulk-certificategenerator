import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    DATABASE_URL: str = "sqlite:///./certificates.db"
    STORAGE_DIR: str = os.path.join(os.getcwd(), "generated_certificates")
    DEFAULT_BATCH_SIZE: int = 50

    model_config = {"env_file": ".env"}

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
