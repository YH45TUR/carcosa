"""
Sistema Legal CO - Jurisprudencia
Endpoints para búsqueda de jurisprudencia en Altas Cortes colombianas.
"""
import os
import json
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import Optional

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter()


@router.post("/search")
async def search_jurisprudence(
    query: str = Body(..., description="Término de búsqueda"),
    fuente: str = Body("suin_juriscol", description="Fuente: suin_juriscol, corte_constitucional, corte_suprema, consejo_estado"),
    max_results: int = Body(5, description="Máximo de resultados"),
    current_user: User = Depends(get_current_user),
):
    """
    Busca jurisprudencia en una Alta Corte colombiana.

    Args:
        query: Término de búsqueda (ej: "derecho a la salud", "nulidad contrato")
        fuente: Fuente a consultar
        max_results: Número máximo de resultados
    """
    from app.modules.jurisprudence.searcher import JurisprudenceSearcher

    searcher = JurisprudenceSearcher()
    result = await searcher.search(
        query=query,
        fuente_id=fuente,
        max_results=max_results,
    )

    return result


@router.post("/search/all")
async def search_all_sources(
    query: str = Body(..., description="Término de búsqueda"),
    max_results: int = Body(3, description="Resultados por fuente"),
    current_user: User = Depends(get_current_user),
):
    """
    Busca jurisprudencia en TODAS las fuentes disponibles simultáneamente.
    """
    from app.modules.jurisprudence.searcher import JurisprudenceSearcher

    searcher = JurisprudenceSearcher()
    result = await searcher.search_all(
        query=query,
        max_results=max_results,
    )

    return result


@router.post("/semantic")
async def semantic_search(
    query: str = Body(..., description="Consulta en lenguaje natural"),
    fuente: str = Body("corte_constitucional", description="Colección semántica"),
    n_results: int = Body(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    """
    Búsqueda semántica de jurisprudencia usando ChromaDB RAG.

    Args:
        query: Consulta en lenguaje natural
        fuente: Colección de vectores
        n_results: Número de resultados
    """
    from app.modules.jurisprudence.rag import JurisprudenceRAG

    rag = JurisprudenceRAG()
    result = await rag.search(
        query=query,
        fuente=fuente,
        n_results=n_results,
    )

    return result


@router.get("/sources")
async def list_sources(
    current_user: User = Depends(get_current_user),
):
    """
    Lista las fuentes de jurisprudencia disponibles.
    """
    from app.modules.jurisprudence.sources import get_all_fuentes, get_fuentes_por_tipo

    all_fuentes = get_all_fuentes()

    return {
        "total": len(all_fuentes),
        "sources": {
            fid: {
                "name": f.nombre,
                "type": f.tipo,
                "primary_url": f.urls[0],
                "has_fallback": len(f.urls) > 1,
            }
            for fid, f in all_fuentes.items()
        },
        "by_type": {
            tipo: [
                {"id": fid, "name": f.nombre}
                for fid, f in get_fuentes_por_tipo(tipo).items()
            ]
            for tipo in set(f.tipo for f in all_fuentes.values())
        },
    }


@router.post("/cache/clear")
async def clear_cache(
    fuente: Optional[str] = Body(None, description="Fuente específica o todas"),
    current_user: User = Depends(require_role([UserRole.admin])),
):
    """
    Limpia el cache de jurisprudencia (solo admin).
    """
    from app.config import settings

    cache_dir = settings.jurisprudence_dir

    if not os.path.exists(cache_dir):
        return {"message": "No hay cache para limpiar"}

    if fuente:
        count = 0
        for filename in os.listdir(cache_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(cache_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if data.get("fuente_id") == fuente:
                        os.remove(filepath)
                        count += 1
                except (json.JSONDecodeError, OSError):
                    pass
        return {"message": f"Cache limpiado: {count} archivos de {fuente}"}
    else:
        count = len([f for f in os.listdir(cache_dir) if f.endswith(".json")])
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            if filename.endswith(".json"):
                os.remove(filepath)
        return {"message": f"Cache limpiado: {count} archivos eliminados"}
