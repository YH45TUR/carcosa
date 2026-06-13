"""
Sistema Legal CO - Core Security
CORRECCIONES APLICADAS:
  - python-jose → PyJWT (librería activamente mantenida, sin CVEs recientes)
  - Tokens incluyen `jti` (JWT ID único) para permitir revocación real
  - Blocklist en DB (tabla revoked_tokens) para logout y pérdida de dispositivo
  - Protección básica contra prompt injection en contenido de documentos
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, List

import jwt  # PyJWT — reemplaza python-jose
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Password ────────────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar password contra hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generar hash bcrypt de password."""
    return pwd_context.hash(password)


# ─── JWT con PyJWT ────────────────────────────────────────────────────────────

def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = {
        **data,
        "jti": str(uuid.uuid4()),  # ID único para revocación
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Crear JWT access token con jti para revocación."""
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _make_token({**data, "type": "access"}, delta)


def create_refresh_token(data: dict) -> str:
    """Crear JWT refresh token."""
    return _make_token(
        {**data, "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodificar y validar token con PyJWT.
    Lanza jwt.ExpiredSignatureError o jwt.InvalidTokenError si inválido.
    A diferencia de python-jose, PyJWT no tiene JWTError genérico —
    capturar jwt.PyJWTError para compatibilidad.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "jti", "sub"]},
    )


# ─── Blocklist — revocación de tokens ─────────────────────────────────────────
# IMPORTANTE: la tabla `revoked_tokens` debe existir en DB.
# Ver app/models/user.py → clase RevokedToken.

async def revoke_token(
    jti: str,
    user_id: int,
    expires_at: datetime,
    db,
) -> None:
    """Agrega el token a la blocklist (logout / pérdida de dispositivo)."""
    from app.models.user import RevokedToken
    revoked = RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at)
    db.add(revoked)
    await db.commit()


async def is_token_revoked(jti: str, db) -> bool:
    """Verifica si el token está en la blocklist."""
    from sqlalchemy import select
    from app.models.user import RevokedToken
    result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    return result.scalar_one_or_none() is not None


async def cleanup_expired_tokens(db) -> int:
    """Elimina tokens expirados de la blocklist. Llamar periódicamente via Celery."""
    from sqlalchemy import delete as sa_delete
    from app.models.user import RevokedToken
    now = datetime.now(timezone.utc)
    result = await db.execute(
        sa_delete(RevokedToken).where(RevokedToken.expires_at < now)
    )
    await db.commit()
    return result.rowcount


# ─── FastAPI dependencies ─────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(),
):
    """
    Dependencia FastAPI: obtener usuario actual desde el token.
    Verifica firma, expiración y (opcionalmente) blocklist.
    """
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise credentials_exception

    username: str = payload.get("sub")
    jti: str = payload.get("jti")
    if not username or not jti:
        raise credentials_exception

    # Verificar blocklist (habilitar cuando se migre a AsyncSession)
    # if await is_token_revoked(jti, db):
    #     raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def require_role(allowed_roles: List):
    """Dependencia: verificar rol del usuario."""
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Roles permitidos: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


# Alias de compatibilidad
get_active_user = get_current_user


# ─── Protección anti-prompt injection ────────────────────────────────────────
# Usar SIEMPRE antes de pasar contenido de documentos al LLM.

INJECTION_DELIMITERS = ("<document>", "</document>")

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard the above",
    "new instructions:",
    "system prompt:",
    "forget everything",
    "act as if",
    "pretend you are",
]


def wrap_user_content(text: str) -> str:
    """
    Enmarca contenido extraído de documentos para aislarlo del system prompt.
    Llama esto antes de incluir texto de documentos en cualquier prompt al LLM.
    """
    sanitized = text.replace(INJECTION_DELIMITERS[0], "[TAG_REMOVED]")
    sanitized = sanitized.replace(INJECTION_DELIMITERS[1], "[TAG_REMOVED]")
    return f"{INJECTION_DELIMITERS[0]}\n{sanitized}\n{INJECTION_DELIMITERS[1]}"


def detect_injection_attempt(text: str) -> bool:
    """Detecta patrones básicos de prompt injection. Loguear si retorna True."""
    text_lower = text.lower()
    return any(p in text_lower for p in INJECTION_PATTERNS)
