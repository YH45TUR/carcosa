"""
Sistema Legal CO - Modelos de Caso
Case, CaseDocument, CaseVersion y relacionados.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class CaseStatus(str, enum.Enum):
    """Estado del caso."""
    activo = "activo"
    archivado = "archivado"
    cerrado = "cerrado"


class LegalArea(str, enum.Enum):
    """Ramas del derecho colombiano."""
    civil = "civil"
    penal = "penal"
    laboral = "laboral"
    administrativo = "administrativo"
    constitucional = "constitucional"
    familia = "familia"
    comercial = "comercial"


class Case(Base):
    """Modelo principal de caso/expediente."""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(50), unique=True, index=True, nullable=True)  # Número de radicado
    cliente = Column(String(200), nullable=False)
    demandado = Column(String(200), nullable=True)  # Parte contraria
    area = Column(SQLEnum(LegalArea), nullable=False)
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.activo)
    juzgado = Column(String(200), nullable=True)
    cuantia = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    # Metadata
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    owner = relationship("User", back_populates="cases")
    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    versions = relationship("CaseVersion", back_populates="case", cascade="all, delete-orphan")
    terms = relationship("CaseTerm", back_populates="case", cascade="all, delete-orphan")
    timeline = relationship("TimelineEvent", back_populates="case", cascade="all, delete-orphan")


class CaseDocument(Base):
    """Documento asociado a un caso."""
    __tablename__ = "case_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, png, jpg
    file_size = Column(Integer, nullable=False)
    
    # Metadatos extraídos
    extracted_text = Column(Text, nullable=True)
    extracted_metadata = Column(Text, nullable=True)  # JSON con entidades
    
    # Chunking para RAG
    chunks = Column(Text, nullable=True)  # JSON array de chunks
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    case = relationship("Case", back_populates="documents")


class CaseVersion(Base):
    """Versión de documento generado."""
    __tablename__ = "case_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # demanda, tutela, recurso, etc.
    version_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)  # Path del DOCX/PDF generado
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    case = relationship("Case", back_populates="versions")


class CaseTerm(Base):
    """Término procesal calculado para un caso."""
    __tablename__ = "case_terms"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    tipo = Column(String(100), nullable=False)  # Caducidad, Prescripción, Término
    norma = Column(String(200), nullable=False)  # Artículos aplicables
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    dias_habiles = Column(Integer, nullable=False)
    code = Column(String(20), nullable=False)  # CGP, CPACA, CPP
    observaciones = Column(Text, nullable=True)
    
    # Estado
    days_remaining = Column(Integer, nullable=True)
    is_expired = Column(Boolean, default=False)
    alert_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    case = relationship("Case", back_populates="terms")


class TimelineEvent(Base):
    """Evento en la línea de tiempo del caso."""
    __tablename__ = "timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    documento_id = Column(Integer, ForeignKey("case_documents.id"), nullable=True)
    tipo = Column(String(50), nullable=False)  # notificación, audiencia, presentación, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    case = relationship("Case", back_populates="timeline")
    documento = relationship("CaseDocument")