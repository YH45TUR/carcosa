"""
Sistema Legal CO - Modelos de Usuario
User, Role y schemas de autenticación.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema."""
    admin = "admin"
    abogado = "abogado"
    asistente = "asistente"


class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.asistente, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cases = relationship("Case", back_populates="owner", lazy="dynamic")
    sessions = relationship("ChatSession", back_populates="user", lazy="dynamic")


# === Pydantic Schemas (no son modelos SQLAlchemy) ===

class Token(BaseModel):
    """Schema para respuesta de tokens JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos contenidos en el token JWT."""
    username: Optional[str] = None


class UserCreate(BaseModel):
    """Schema para registro de usuario."""
    username: str
    email: str
    password: str
    role: str = "asistente"


class UserResponse(BaseModel):
    """Schema para respuesta pública de usuario."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
