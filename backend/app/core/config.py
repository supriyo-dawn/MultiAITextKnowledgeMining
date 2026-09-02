"""
Configuration management using Pydantic Settings.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    DEBUG: bool = False
    APP_NAME: str = "Multi-AI Knowledge Graph System"
    APP_VERSION: str = "0.1.0"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Document Processing
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # "openai" or "ollama"
    LLM_MODEL: str = "gpt-4"
    OPENAI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Vector Store
    VECTOR_DB_PATH: str = "data/vector_store"
    FAISS_INDEX_PATH: str = "data/faiss_index.bin"

    # Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    CONFIDENCE_THRESHOLD: float = 0.7

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
