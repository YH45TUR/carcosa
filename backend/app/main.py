"""
Sistema Legal CO - FastAPI Application
Punto de entrada principal de la API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

import os

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - startup y shutdown."""
    # Startup
    print(f"Iniciando {settings.app_name}...")
    init_db()
    print("✓ Base de datos inicializada")
    yield
    # Shutdown
    print("Apagando sistema...")


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
    return {
        "app": settings.app_name,
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}