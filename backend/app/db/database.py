"""
Sistema Legal CO - Database Setup
SQLAlchemy engine con soporte para SQLite (dev) y PostgreSQL (prod).
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Crear engine desde DATABASE_URL
# SQLite: sin pool. PostgreSQL: pool de conexiones
_is_sqlite = "sqlite" in settings.database_url

engine_kwargs = {
    "echo": settings.debug,
}

if _is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.database_pool_size
    engine_kwargs["max_overflow"] = settings.database_max_overflow
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.database_url, **engine_kwargs)

# SessionLocal para dependencias FastAPI
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI para obtener sesión de DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa la base de datos - crea todas las tablas."""
    Base.metadata.create_all(bind=engine)