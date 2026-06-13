"""
Sistema Legal CO - Configuración Central
Todas las variables de entorno y configuración del sistema.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    # SQLite para desarrollo, PostgreSQL para producción
    database_url: str = "sqlite:///./sistema_legal.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # LLM
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    gemini_api_key: str = ""
    claude_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    
    # Autenticación JWT
    jwt_secret: str = "cambiar_en_produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    
    # RAG / Vector Store
    chroma_persist_directory: str = "./data/chroma"
    embedding_model: str = "mxbai-embed-large"
    
    # Rutas
    uploads_dir: str = "./data/uploads"
    jurisprudence_dir: str = "./data/jurisprudence"
    
    # App
    app_name: str = "Sistema Legal CO"
    debug: bool = True
    cors_origins: str = "*"
    log_level: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()