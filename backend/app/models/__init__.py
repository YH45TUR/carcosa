"""
Sistema Legal CO - Modelos
Importación explícita de todos los modelos para que SQLAlchemy pueda
resolver relaciones lazy (string-based) correctamente.
"""
from app.models.user import User, UserRole, Token, TokenData
from app.models.case import Case, CaseStatus, LegalArea, CaseDocument, CaseVersion, CaseTerm, TimelineEvent
from app.models.chat import ChatSession, ChatMessage
from app.models.document import DocumentTemplate
