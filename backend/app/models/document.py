"""
Sistema Legal CO - Modelos de Documento
Modelos adicionales para gestión de documentos y plantillas.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class DocumentTemplate(Base):
    """Plantilla de documento legal reutilizable."""
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)  # demanda, tutela, etc.
    content = Column(Text, nullable=False)  # Jinja2 template
    description = Column(String(500), nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
