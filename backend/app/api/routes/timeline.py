"""
Sistema Legal CO - Timeline
Endpoints para extracción y visualización de cronología de casos.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.modules.timeline.extractor import TimelineExtractor

router = APIRouter()
extractor = TimelineExtractor()


@router.post("/from-case/{case_id}")
async def timeline_from_case(
    case_id: int,
    case_data: Dict[str, Any] = Body(..., description="Datos completos del caso"),
    current_user: User = Depends(get_current_user),
):
    """
    Extrae y genera la cronología de un caso a partir de sus datos.
    """
    result = await extractor.extract_from_case(case_data)
    return {
        "success": True,
        "response": result["resumen"],
        "data": result,
    }


@router.post("/from-text")
async def timeline_from_text(
    text: str = Body(..., description="Texto del documento legal"),
    current_user: User = Depends(get_current_user),
):
    """
    Extrae cronología del texto de un documento legal.
    """
    if len(text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Texto demasiado corto (mín. 50 caracteres)"
        )

    result = await extractor.extract_from_text(text)
    return {
        "success": True,
        "response": result["resumen"],
        "data": result,
    }
