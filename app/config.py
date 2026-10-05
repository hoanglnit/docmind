from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DocMind"
    app_host: str = "0.0.0.0"
    app_port: int = 7860
    debug: bool = False

    database_url: str = f"sqlite:///{BASE_DIR}/storage/docmind.db"
    upload_dir: Path = BASE_DIR / "storage" / "uploads"
    chroma_dir: Path = BASE_DIR / "storage" / "chroma"

    ollama_base_url: str = "http://localhost:11434/v1"
    model_name: str = "gemma4:e4b"
    max_tokens: int = 2048
    temperature: float = 0.7

    embedding_model: str = "all-MiniLM-L6-v2"

    default_top_k: int = 5
    chunk_size: int = 1500
    chunk_overlap: int = 200


settings = Settings()
