"""
Sistema Legal CO - FastAPI Application
Punto de entrada principal de la API.
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.database import init_db
from app.api.routes import (
    auth,
    cases,
    chat,
    documents,
    export,
    audit,
    jurisprudence,
    diagram,
    adversarial,
    calculator,
    timeline
)

# ─── Logging estructurado ────────────────────────────────────────────────────
logger = logging.getLogger("sistema-legal")
logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

# Evitar duplicación de handlers en re-imports
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(console_handler)
    logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - startup y shutdown."""
    logger.info("Iniciando %s...", settings.app_name)
    init_db()
    logger.info("Base de datos inicializada")
    logger.debug("Modo debug activado - conexiones DB: pool=%d, overflow=%d",
                 settings.database_pool_size, settings.database_max_overflow)
    yield
    logger.info("Apagando sistema...")


# Rate limiter por IP (deshabilitado en testing para no romper tests)
_is_testing = os.environ.get("TESTING", "").lower() == "true"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_default_per_minute}/minute"] if not _is_testing else ["1000/minute"],
    enabled=not _is_testing
)

app = FastAPI(
    title=settings.app_name,
    description="Sistema integral de gestión legal con IA para abogados colombianos",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (va despues de CORS)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(cases.router, prefix="/api/cases", tags=["Casos"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documentos"])
app.include_router(export.router, prefix="/api/export", tags=["Exportación"])
app.include_router(audit.router, prefix="/api/audit", tags=["Auditoría"])
app.include_router(jurisprudence.router, prefix="/api/jurisprudence", tags=["Jurisprudencia"])
app.include_router(diagram.router, prefix="/api/diagram", tags=["Diagramas"])
app.include_router(adversarial.router, prefix="/api/adversarial", tags=["Análisis Adversarial"])
app.include_router(calculator.router, prefix="/api/calculator", tags=["Calculadora de Términos"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["Timeline"])


@app.get("/")
async def root():
    logger.debug("Health check desde %s", "/")
    return {
        "app": settings.app_name,
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ─── Exponer logger para otros módulos ────────────────────────────────────────
def get_logger(name: str = None) -> logging.Logger:
    """Obtiene un logger con el nombre del módulo."""
    return logging.getLogger(f"sistema-legal.{name}") if name else logger