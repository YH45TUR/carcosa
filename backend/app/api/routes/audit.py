"""
Sistema Legal CO - Auditoría Legal
Endpoints para auditoría de documentos y casos legales.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.case import Case
from app.modules.audit.auditor import LegalAuditor

router = APIRouter()


@router.post("/case/{case_id}")
async def audit_case(
    case_id: int,
    message: str = Body("", description="Instrucciones adicionales para la auditoría"),
    codigo: str = Body("CGP", description="Código procesal: CGP, CPACA, CPP"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Audita un caso completo incluyendo sus documentos asociados.

    Args:
        case_id: ID del caso a auditar
        message: Instrucciones o enfoque de la auditoría
        codigo: Código procesal para las reglas (CGP, CPACA, CPP)
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    # Buscar documentos del caso para incluir en la auditoría
    documents_text = None
    if case.documents:
        texts = []
        for doc in case.documents:
            if doc.extracted_text:
                texts.append(f"--- {doc.original_filename} ---\n{doc.extracted_text[:5000]}")
        if texts:
            documents_text = "\n\n".join(texts)

    auditor = LegalAuditor()
    result = await auditor.audit_case(
        case_id=case_id,
        message=message or f"Auditar caso {case.radicado or case_id}",
        document_text=documents_text,
    )

    return result


@router.post("/document")
async def audit_document(
    text: str = Body(..., description="Texto del documento a auditar"),
    codigo: str = Body("CGP", description="Código procesal: CGP, CPACA, CPP"),
    current_user: User = Depends(get_current_user),
):
    """
    Audita el texto de un documento legal.

    Args:
        text: Contenido del documento
        codigo: Código procesal (CGP, CPACA, CPP)
    """
    if len(text) < 50:
        raise HTTPException(
            status_code=400,
            detail="El texto es demasiado corto para una auditoría significativa (mín. 50 caracteres)"
        )

    auditor = LegalAuditor()
    result = await auditor.audit_document(
        document_text=text,
        codigo=codigo.upper(),
    )

    return result


@router.get("/reglas")
async def list_rules(
    codigo: Optional[str] = Query(None, description="Filtrar por código: CGP, CPACA, CPP"),
    criticidad: Optional[str] = Query(None, description="Filtrar por criticidad: crítico, alto, medio, bajo"),
):
    """
    Lista las reglas de auditoría disponibles.
    """
    from app.modules.audit.rules import ReglasAuditoria, Criticidad

    rules = ReglasAuditoria.get_all_rules()

    if codigo:
        rules = ReglasAuditoria.get_rules_by_code(codigo)

    if criticidad:
        try:
            c = Criticidad(criticidad)
            rules = [r for r in rules if r.criticidad == c]
        except ValueError:
            pass

    return {
        "total": len(rules),
        "reglas": [
            {
                "codigo": r.codigo,
                "criticidad": r.criticidad.value,
                "categoria": r.categoria.value if r.categoria else "general",
                "titulo": r.titulo,
                "norma": r.norma,
                "automatizable": r.automatizable,
            }
            for r in rules
        ],
    }
