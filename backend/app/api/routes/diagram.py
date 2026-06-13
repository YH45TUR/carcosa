"""
Sistema Legal CO - Diagramas Legales
Endpoints para generación de diagramas Mermaid.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.modules.diagram.generator import DiagramGenerator

router = APIRouter()
generator = DiagramGenerator()


@router.post("/generate")
async def generate_diagram(
    tipo: str = Body(..., description="Tipo: timeline, flowchart, graph"),
    data: Dict[str, Any] = Body(..., description="Datos para el diagrama"),
    current_user: User = Depends(get_current_user),
):
    """
    Genera un diagrama Mermaid a partir de datos.

    Tipos:
    - timeline: Línea de tiempo procesal (events[])
    - flowchart: Árbol de decisión (nodes[], edges[])
    - graph: Mapa de partes (partes[])
    """
    try:
        result = await generator.generate(tipo, data)
        return {
            "success": True,
            "chart": result["chart"],
            "type": result["type"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-case/{case_id}")
async def diagram_from_case(
    case_id: int,
    tipo: str = Body("timeline", description="Tipo de diagrama"),
    case_data: Dict[str, Any] = Body(..., description="Datos del caso"),
    current_user: User = Depends(get_current_user),
):
    """
    Genera diagrama automáticamente desde datos de un caso.
    """
    result = await generator.generate_from_case(case_data, tipo)
    return {
        "success": True,
        "chart": result["chart"],
        "type": result["type"],
    }
