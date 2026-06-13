"""
Sistema Legal CO - Calculadora de Términos Procesales
Endpoints para cálculo de días hábiles, caducidad, prescripción y alertas.
"""
from fastapi import APIRouter, Depends, Body, Query
from typing import Optional
from datetime import date, datetime

from app.core.security import get_current_user
from app.models.user import User
from app.modules.calculator.terms import CalculadoraTerminos

router = APIRouter()
calculadora = CalculadoraTerminos()


@router.post("/calcular")
async def calcular_termino(
    tipo: str = Body(..., description="Tipo de término: traslado_demanda, caducidad_verbal, etc."),
    codigo: str = Body("CGP", description="Código: CGP, CPACA, CPP"),
    fecha_inicio: str = Body(..., description="Fecha de inicio (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
):
    """
    Calcula un término procesal desde una fecha de inicio.

    Args:
        tipo: Tipo de término (ver /lista)
        codigo: Código procesal
        fecha_inicio: Fecha de inicio del término
    """
    try:
        fecha = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "response": "Formato de fecha inválido. Usa YYYY-MM-DD",
        }

    try:
        resultado = await calculadora.calcular(tipo, codigo, fecha)
        return {
            "success": True,
            "response": _format_resultado(resultado),
            "data": resultado.to_dict(),
        }
    except ValueError as e:
        return {
            "success": False,
            "response": str(e),
        }


@router.post("/alertas/{case_id}")
async def alertas_caso(
    case_id: int,
    terminos: list = Body(..., description="Lista de términos calculados"),
    current_user: User = Depends(get_current_user),
):
    """
    Evalúa alertas para términos de un caso.

    Args:
        case_id: ID del caso
        terminos: Lista de términos calculados previamente
    """
    from app.models.case import CaseTerm
    from app.db.database import SessionLocal

    alertas = []
    for t in terminos:
        try:
            fecha_fin = datetime.strptime(t["fecha_fin"], "%Y-%m-%d").date()
            fecha_inicio = datetime.strptime(t["fecha_inicio"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue

        dias_restantes = (fecha_fin - date.today()).days
        vencido = dias_restantes < 0
        urgente = 0 <= dias_restantes <= 5

        alertas.append({
            "tipo": t.get("tipo", "procesal"),
            "codigo": t.get("codigo", "CGP"),
            "fecha_fin": t["fecha_fin"],
            "days_remaining": dias_restantes,
            "is_expired": vencido,
            "is_urgent": urgente,
            "alerta": (
                f"🔴 VENCIDO - Hace {abs(dias_restantes)} días"
                if vencido
                else f"⚠️ URGENTE - Vence en {dias_restantes} días"
                if urgente
                else f"✅ Vigente - {dias_restantes} días restantes"
            ),
        })

    return {
        "total_alertas": len(alertas),
        "vencidos": len([a for a in alertas if a["is_expired"]]),
        "urgentes": len([a for a in alertas if a["is_urgent"]]),
        "alertas": alertas,
    }


@router.get("/lista")
async def listar_terminos(
    codigo: Optional[str] = Query(None, description="Filtrar por código: CGP, CPACA, CPP"),
    current_user: User = Depends(get_current_user),
):
    """
    Lista los términos procesales disponibles para cálculo.
    """
    terminos = await calculadora.listar_terminos(codigo)
    return {
        "total": len(terminos),
        "codigos": list(set(t["codigo"] for t in terminos)),
        "terminos": terminos,
    }


def _format_resultado(resultado) -> str:
    """Formatea el resultado del cálculo."""
    lines = [
        f"📅 Cálculo de Término Procesal",
        f"",
        f"Tipo: {resultado.tipo}",
        f"Código: {resultado.codigo}",
        f"Norma: {resultado.norma}",
        f"",
        f"Fecha inicio: {resultado.fecha_inicio.strftime('%d/%m/%Y')}",
        f"Fecha fin: {resultado.fecha_fin.strftime('%d/%m/%Y')}",
        f"Días hábiles: {resultado.dias_habiles}",
        f"Días calendario: {resultado.dias_calendario}",
        f"",
        f"{resultado._generar_alerta()}",
    ]
    return "\n".join(lines)
