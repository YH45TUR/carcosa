"""
Sistema Legal CO - Fuentes de Jurisprudencia Colombiana
URLs oficiales de Altas Cortes con lista de fallbacks por fuente.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FuenteJurisprudencia:
    """Configuración de una fuente de jurisprudencia."""
    id: str
    nombre: str
    urls: List[str]  # URLs con fallbacks
    tipo: str  # constitucional, casacion, contencioso, normativa
    formato_busqueda: str  # query string format
    cache_ttl_hours: int = 24
    timeout_seconds: int = 15
    headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "es-CO,es;q=0.9",
    })


# ============================================
# Fuentes oficiales de jurisprudencia colombiana
# ============================================

FUENTES: Dict[str, FuenteJurisprudencia] = {
    "corte_constitucional": FuenteJurisprudencia(
        id="corte_constitucional",
        nombre="Corte Constitucional de Colombia",
        urls=[
            "https://www.corteconstitucional.gov.co/relatoria/",
            "https://www.corteconstitucional.gov.co/",
        ],
        tipo="constitucional",
        formato_busqueda="?buscar={query}",
        cache_ttl_hours=48,
    ),
    "corte_suprema": FuenteJurisprudencia(
        id="corte_suprema",
        nombre="Corte Suprema de Justicia - Relatoría",
        urls=[
            "https://consultajurisprudencial.ramajudicial.gov.co/WebRelatoria/csj/index.xhtml",
            "https://cortesuprema.gov.co/",
        ],
        tipo="casacion",
        formato_busqueda="?buscar={query}",
        cache_ttl_hours=48,
    ),
    "consejo_estado": FuenteJurisprudencia(
        id="consejo_estado",
        nombre="Consejo de Estado de Colombia",
        urls=[
            "https://www.consejodeestado.gov.co/buscador-de-jurisprudencia2/index.htm",
            "https://www.consejodeestado.gov.co/",
        ],
        tipo="contencioso",
        formato_busqueda="?query={query}",
        cache_ttl_hours=48,
    ),
    "suin_juriscol": FuenteJurisprudencia(
        id="suin_juriscol",
        nombre="SUIN-JURISCOL - Sistema Único de Información Normativa",
        urls=[
            "https://www.suin-juriscol.gov.co/jurisprudencia/jurisprudencia.html",
            "https://www.suin-juriscol.gov.co/",
        ],
        tipo="normativa",
        formato_busqueda="?q={query}",
        cache_ttl_hours=72,
    ),
}


def get_fuente(fuente_id: str) -> FuenteJurisprudencia:
    """Obtiene una fuente por su ID."""
    if fuente_id not in FUENTES:
        raise ValueError(
            f"Fuente '{fuente_id}' no encontrada. "
            f"Disponibles: {', '.join(FUENTES.keys())}"
        )
    return FUENTES[fuente_id]


def get_fuentes_por_tipo(tipo: str) -> Dict[str, FuenteJurisprudencia]:
    """Obtiene fuentes filtradas por tipo."""
    return {
        fid: f for fid, f in FUENTES.items()
        if f.tipo == tipo
    }


def get_all_fuentes() -> Dict[str, FuenteJurisprudencia]:
    """Obtiene todas las fuentes disponibles."""
    return FUENTES


def get_url_primaria(fuente_id: str) -> str:
    """Obtiene la URL principal de una fuente."""
    fuente = get_fuente(fuente_id)
    return fuente.urls[0] if fuente.urls else ""


def get_url_fallback(fuente_id: str) -> Optional[str]:
    """Obtiene la URL de respaldo de una fuente."""
    fuente = get_fuente(fuente_id)
    return fuente.urls[1] if len(fuente.urls) > 1 else None
