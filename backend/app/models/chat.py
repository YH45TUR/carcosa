"""
Sistema Legal CO - Modelos de Chat
ChatSession y mensajes para memoria conversacional.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class ChatSession(Base):
    """Sesión de chat asociada a un usuario y opcionalmente a un caso."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    title = Column(String(200), nullable=True)
    context = Column(JSON, nullable=True)  # Estado conversacional
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="dynamic")


class ChatMessage(Base):
    """Mensaje individual dentro de una sesión de chat."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    module = Column(String(50), nullable=True)  # drafting, audit, etc.
    metadata_json = Column(JSON, nullable=True)  # Datos extra asociados

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    session = relationship("ChatSession", back_populates="messages")
