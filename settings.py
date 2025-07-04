from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = "1234567890"
    COLPALI_MODEL_NAME: str = "vidore/colpali-v1.2"
    BATCH_SIZE: int = 16
    IMAGE_SEQ_LENGTH: int = 1024

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
