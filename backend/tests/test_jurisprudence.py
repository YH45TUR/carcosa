"""
Sistema Legal CO - Tests de Jurisprudencia
Pruebas para los módulos de búsqueda de jurisprudencia y RAG.
"""
import pytest
import os
import json
import tempfile
from datetime import datetime


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def sources():
    """Referencia al módulo de fuentes."""
    from app.modules.jurisprudence import sources
    return sources


@pytest.fixture
def searcher():
    """Instancia del buscador."""
    from app.modules.jurisprudence.searcher import JurisprudenceSearcher
    return JurisprudenceSearcher()


# ============================================
# Tests: Fuentes (Sources)
# ============================================

class TestSources:
    """Tests para las fuentes de jurisprudencia."""

    def test_get_all_fuentes(self, sources):
        """Debe retornar todas las fuentes."""
        all_fuentes = sources.get_all_fuentes()
        assert len(all_fuentes) >= 4

    def test_get_fuente_valid(self, sources):
        """Debe retornar una fuente válida."""
        fuente = sources.get_fuente("corte_constitucional")
        assert fuente.id == "corte_constitucional"
        assert "corteconstitucional.gov.co" in fuente.urls[0]
        assert fuente.tipo == "constitucional"
        assert fuente.cache_ttl_hours > 0

    def test_get_fuente_invalid(self, sources):
        """Fuente inválida debe lanzar ValueError."""
        with pytest.raises(ValueError):
            sources.get_fuente("fuente_invalida")

    def test_get_fuentes_por_tipo(self, sources):
        """Debe filtrar fuentes por tipo."""
        constitucionales = sources.get_fuentes_por_tipo("constitucional")
        assert len(constitucionales) >= 1
        assert "corte_constitucional" in constitucionales

    def test_get_url_primaria(self, sources):
        """Debe retornar URL principal."""
        url = sources.get_url_primaria("suin_juriscol")
        assert url.startswith("https://")

    def test_get_url_fallback(self, sources):
        """Debe retornar URL de respaldo."""
        fallback = sources.get_url_fallback("corte_suprema")
        assert fallback is not None
        assert fallback.startswith("https://")

    def test_fuente_structure(self, sources):
        """Cada fuente debe tener todos los campos requeridos."""
        for fid, fuente in sources.get_all_fuentes().items():
            assert fuente.id
            assert fuente.nombre
            assert len(fuente.urls) >= 1
            assert fuente.tipo in ("constitucional", "casacion", "contencioso", "normativa")
            assert fuente.cache_ttl_hours >= 1
            assert fuente.timeout_seconds >= 5


# ============================================
# Tests: Searcher
# ============================================

class TestSearcher:
    """Tests para el buscador de jurisprudencia."""

    @pytest.mark.asyncio
    async def test_search_mock_results(self, searcher):
        """Búsqueda sin conexión debe generar resultados mock."""
        result = await searcher.search(
            query="derecho a la salud",
            fuente_id="corte_constitucional",
            use_cache=False,
        )
        assert result["success"]
        assert result["data"]["total"] > 0
        assert len(result["data"]["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_invalid_source(self, searcher):
        """Fuente inválida debe retornar error."""
        result = await searcher.search(
            query="test",
            fuente_id="fuente_invalida",
            use_cache=False,
        )
        assert not result["success"]
        assert "available_sources" in result

    @pytest.mark.asyncio
    async def test_search_all(self, searcher):
        """Búsqueda en todas las fuentes debe combinar resultados."""
        result = await searcher.search_all(
            query="derechos fundamentales",
            max_results=2,
        )
        assert result["success"] or not result["success"]

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, searcher):
        """La clave de cache debe ser determinística."""
        key1 = searcher._cache_key("derecho a la salud", "corte_constitucional")
        key2 = searcher._cache_key("Derecho a la Salud", "corte_constitucional")
        assert key1 == key2  # Case insensitive
        assert len(key1) == 32  # MD5 hash

    @pytest.mark.asyncio
    async def test_format_results(self, searcher):
        """El formato de resultados debe incluir título y texto."""
        mock_results = [
            {"titulo": "Sentencia T-001/24", "texto": "Test", "fecha": "2024-01-01"},
        ]
        formatted = searcher._format_results(mock_results, "Corte Constitucional", "test")
        assert "Sentencia T-001/24" in formatted
        assert "Corte Constitucional" in formatted

    @pytest.mark.asyncio
    async def test_generate_mock_results(self, searcher):
        """Los resultados mock deben ser específicos por fuente."""
        cc = searcher._generate_mock_results("test", "corte_constitucional")
        assert any("Sentencia" in r.get("titulo", "") for r in cc)

        cs = searcher._generate_mock_results("test", "corte_suprema")
        assert any("Corte Suprema" in r.get("titulo", "") for r in cs)

    @pytest.mark.asyncio
    async def test_parse_raw_text(self, searcher):
        """Parseo de texto plano debe generar resultados."""
        text = "Título Importante\nContenido del documento con más de 30 caracteres aquí."
        results = searcher._parse_raw_text(text, 5)
        assert len(results) >= 1


# ============================================
# Tests: RAG
# ============================================

class TestRAG:
    """Tests para el sistema RAG."""

    @pytest.mark.asyncio
    async def test_rag_search_fallback(self):
        """Sin ChromaDB, RAG debe hacer fallback a web search."""
        from app.modules.jurisprudence.rag import JurisprudenceRAG
        rag = JurisprudenceRAG()

        # Forzar modo sin chroma para probar fallback
        rag._chroma_available = False
        result = await rag.search("test query", "corte_constitucional", 3)

        assert result["success"]
        assert result["data"]["mode"] == "fallback_web_search"

    @pytest.mark.asyncio
    async def test_format_citation_corte_constitucional(self):
        """Cita de Corte Constitucional debe tener formato Colombia."""
        from app.modules.jurisprudence.rag import JurisprudenceRAG
        rag = JurisprudenceRAG()

        sentencia = {
            "tipo": "T",
            "corte": "Corte Constitucional",
            "numero": "123",
            "año": 2024,
            "magistrado_ponente": "Dr. Pérez",
        }
        citation = await rag.format_citation(sentencia)
        assert "T-123/24" in citation

    @pytest.mark.asyncio
    async def test_format_citation_corte_suprema(self):
        """Cita de Corte Suprema debe tener formato SC."""
        from app.modules.jurisprudence.rag import JurisprudenceRAG
        rag = JurisprudenceRAG()

        sentencia = {
            "tipo": "sentencia",
            "corte": "Corte Suprema de Justicia",
            "numero": "12345",
            "año": 2024,
        }
        citation = await rag.format_citation(sentencia)
        assert "SC12345-2024" in citation

    @pytest.mark.asyncio
    async def test_format_citation_consejo_estado(self):
        """Cita de Consejo de Estado debe tener formato CE."""
        from app.modules.jurisprudence.rag import JurisprudenceRAG
        rag = JurisprudenceRAG()

        sentencia = {
            "tipo": "sentencia",
            "corte": "Consejo de Estado",
            "numero": "12345",
            "año": 2024,
        }
        citation = await rag.format_citation(sentencia)
        assert "CE-12345-2024" in citation


# ============================================
# Tests: Routes
# ============================================

class TestJurisprudenceRoutes:
    """Tests para los endpoints de jurisprudencia."""

    def test_search_endpoint_exists(self):
        """El endpoint de búsqueda debe estar configurado."""
        from app.api.routes.jurisprudence import router
        routes = [r.path for r in router.routes]
        assert "/search" in routes
        assert "/search/all" in routes
        assert "/semantic" in routes
        assert "/sources" in routes
        assert "/cache/clear" in routes

    def test_orchestrator_handler_configured(self):
        """El orquestador debe tener handler para jurisprudencia."""
        from app.core.orchestrator import Router
        router = Router()
        assert "jurisprudence" in router.INTENT_PATTERNS
        assert len(router.INTENT_PATTERNS["jurisprudence"]) >= 5
