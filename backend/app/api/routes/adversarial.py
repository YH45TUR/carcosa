"""
Sistema Legal CO - Análisis Adversarial
Endpoints para análisis desde perspectivas de juez y contra-parte.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.case import Case
from app.modules.adversarial.analyzer import AdversarialAnalyzer
from app.modules.adversarial.prompts import get_available_perspectives

router = APIRouter()

analyzer = AdversarialAnalyzer()


@router.post("/analyze/{case_id}")
async def analyze_case(
    case_id: int,
    perspective: str = Query("judge", description="Perspectiva: judge u opponent"),
    message: str = Body("", description="Mensaje adicional para contextualizar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza un caso desde una perspectiva adversarial.

    Args:
        case_id: ID del caso
        perspective: 'judge' (Ojo del Juez) u 'opponent' (Contra-Parte Virtual)
        message: Contexto adicional
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    # Construir texto del caso
    case_data = {
        "cliente": case.cliente,
        "demandado": case.demandado,
        "radicado": case.radicado,
        "area": case.area.value if case.area else None,
        "juzgado": case.juzgado,
        "status": case.status.value if case.status else None,
    }

    # Obtener textos de documentos asociados
    document_text = message
    if case.documents:
        texts = []
        for doc in case.documents[:3]:  # Máximo 3 documentos
            if doc.extracted_text:
                texts.append(doc.extracted_text[:5000])
        if texts:
            document_text = message + "\n\n" + "\n\n".join(texts)

    if not document_text:
        raise HTTPException(
            status_code=400,
            detail="No hay suficiente texto para analizar. Agrega un mensaje o sube documentos al caso."
        )

    result = await analyzer.analyze(
        document_text=document_text,
        perspective=perspective,
        case_data=case_data,
    )

    return result


@router.post("/analyze/text")
async def analyze_text(
    text: str = Body(..., description="Texto del documento legal a analizar"),
    perspective: str = Query("judge", description="Perspectiva: judge u opponent"),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza texto libre desde una perspectiva adversarial.

    Args:
        text: Contenido del documento
        perspective: 'judge' u 'opponent'
    """
    if len(text) < 100:
        raise HTTPException(
            status_code=400,
            detail="El texto debe tener al menos 100 caracteres para un análisis significativo"
        )

    result = await analyzer.analyze(
        document_text=text,
        perspective=perspective,
    )

    return result


@router.post("/analyze/both/{case_id}")
async def analyze_both_perspectives(
    case_id: int,
    message: str = Body("", description="Contexto adicional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza un caso desde ambas perspectivas simultáneamente (juez + contra-parte).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    document_text = message
    if case.documents:
        texts = []
        for doc in case.documents[:3]:
            if doc.extracted_text:
                texts.append(doc.extracted_text[:5000])
        if texts:
            document_text = message + "\n\n" + "\n\n".join(texts)

    result = await analyzer.analyze_both(
        document_text=document_text or "Sin texto adicional",
        case_data={
            "cliente": case.cliente,
            "demandado": case.demandado,
            "radicado": case.radicado,
        },
    )

    return result


@router.get("/perspectives")
async def list_perspectives():
    """
    Lista las perspectivas disponibles para el análisis adversarial.
    """
    return {
        "perspectives": get_available_perspectives(),
        "total": len(get_available_perspectives()),
    }
