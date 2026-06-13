"""
Sistema Legal CO - Tests de Extracción
Pruebas unitarias para el pipeline de extracción de documentos usando pytest.

Referencia: skills/pytest/SKILL.md
- Usar fixtures para compartir estado
- @pytest.mark.asyncio para tests async
- @pytest.mark.parametrize para múltiples escenarios
"""
import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def sample_pdf_text():
    """Texto simulado de un PDF legal colombiano."""
    return (
        "JUZGADO PRIMERO CIVIL DEL CIRCUITO DE BOGOTÁ\n\n"
        "Radicado: 11001-31-03-001-2024-00001-00\n\n"
        "DEMANDANTE: JUAN PÉREZ LÓPEZ\n"
        "DEMANDADO: MARÍA GARCÍA RUIZ\n\n"
        "HECHOS\n\n"
        "Primero: El día 15 de marzo de 2024, las partes suscribieron un contrato "
        "de compraventa por la suma de $200.000.000 millones de pesos.\n\n"
        "FUNDAMENTOS DE DERECHO\n\n"
        "Artículo 1501 del Código Civil, Ley 820 de 2003.\n\n"
        "RESUELVE\n\n"
        "Primero: Declarar no probadas las excepciones propuestas."
    )


@pytest.fixture
def sample_radicados():
    """Muestra de radicados colombianos para testing."""
    return [
        "11001-31-03-001-2024-00001-00",
        "05001-31-03-001-2023-12345-01",
        "76001-31-03-001-2024-00001-00",
    ]


@pytest.fixture
def sample_juzgados():
    """Muestra de juzgados colombianos para testing."""
    return [
        "Juzgado 1° Civil del Circuito de Bogotá",
        "Juzgado 2 Penal Municipal de Medellín",
        "Tribunal Superior de Cali",
    ]


@pytest.fixture
def ner_instance():
    """Instancia de LegalNER con spaCy mockeado."""
    from app.modules.extraction.ner import LegalNER
    ner = LegalNER()
    # Mock para que no intente cargar spaCy
    ner._spacy_available = False
    return ner


@pytest.fixture
def temp_pdf_file():
    """Crea un archivo PDF temporal para testing."""
    # Crear un PDF mínimo válido
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================
# Tests: PDFParser
# ============================================

class TestPDFParser:
    """Tests para el parser de PDF."""

    @pytest.mark.asyncio
    async def test_extract_text_no_file(self):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        from app.modules.extraction.pdf_parser import PDFParser
        parser = PDFParser()

        with pytest.raises(FileNotFoundError):
            await parser.extract_text("/ruta/inexistente.pdf")

    @pytest.mark.asyncio
    async def test_get_metadata_no_file(self):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        from app.modules.extraction.pdf_parser import PDFParser
        parser = PDFParser()

        with pytest.raises(FileNotFoundError):
            await parser.extract_pages("/ruta/inexistente.pdf")

    @pytest.mark.asyncio
    async def test_get_metadata_with_temp_file(self, temp_pdf_file):
        """Debe retornar metadatos básicos incluso sin motor PDF."""
        from app.modules.extraction.pdf_parser import PDFParser
        parser = PDFParser()

        metadata = await parser.get_metadata(temp_pdf_file)
        assert metadata["filename"].endswith(".pdf")
        assert metadata["file_size"] > 0

    @pytest.mark.parametrize("page_num", [1, 2, 3])
    @pytest.mark.asyncio
    async def test_extract_pages_with_invalid_file(self, page_num):
        """Debe fallar con páginas de archivos inexistentes."""
        from app.modules.extraction.pdf_parser import PDFParser
        parser = PDFParser()

        with pytest.raises(FileNotFoundError):
            await parser.extract_pages(f"/ruta/test_page_{page_num}.pdf")


class TestDOCXParser:
    """Tests para el parser de DOCX."""

    @pytest.mark.asyncio
    async def test_extract_text_no_file(self):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        from app.modules.extraction.docx_parser import DOCXParser
        parser = DOCXParser()

        with pytest.raises(FileNotFoundError):
            await parser.extract_text("/ruta/inexistente.docx")

    @pytest.mark.asyncio
    async def test_extract_structured_no_file(self):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        from app.modules.extraction.docx_parser import DOCXParser
        parser = DOCXParser()

        with pytest.raises(FileNotFoundError):
            await parser.extract_structured("/ruta/inexistente.docx")


# ============================================
# Tests: LegalNER
# ============================================

class TestLegalNER:
    """Tests para el extractor de entidades legales."""

    @pytest.mark.asyncio
    async def test_extract_entities_empty_text(self, ner_instance):
        """Texto vacío debe retornar resultado vacío."""
        result = await ner_instance.extract_entities("")
        assert result["total_entities"] == 0
        assert result["radicados"] == []

    @pytest.mark.asyncio
    async def test_extract_entities_none_text(self, ner_instance):
        """None debe retornar resultado vacío."""
        result = await ner_instance.extract_entities(None)
        assert result["total_entities"] == 0

    @pytest.mark.asyncio
    async def test_extract_radicado(self, ner_instance, sample_pdf_text):
        """Debe extraer radicados correctamente."""
        result = await ner_instance.extract_entities(sample_pdf_text)
        assert len(result["radicados"]) > 0
        assert "11001-31-03-001-2024-00001-00" in [r["value"] for r in result["radicados"]]

    @pytest.mark.asyncio
    async def test_extract_juzgado(self, ner_instance, sample_pdf_text):
        """Debe extraer juzgados correctamente."""
        result = await ner_instance.extract_entities(sample_pdf_text)
        assert len(result["juzgados"]) > 0
        assert any("juzgado" in j["value"].lower() for j in result["juzgados"])

    @pytest.mark.asyncio
    async def test_extract_normas(self, ner_instance, sample_pdf_text):
        """Debe extraer normas legales citadas."""
        result = await ner_instance.extract_entities(sample_pdf_text)
        assert len(result["normas"]) > 0
        normas_values = [n["value"] for n in result["normas"]]
        assert any("Ley" in n for n in normas_values) or any("Artículo" in n for n in normas_values)

    @pytest.mark.asyncio
    async def test_extract_fechas(self, ner_instance):
        """Debe extraer fechas en formato colombiano."""
        text = "El día 15 de marzo de 2024 se presentó la demanda."
        result = await ner_instance.extract_entities(text)
        assert len(result["fechas"]) > 0
        assert "15 de marzo de 2024" in [f["value"] for f in result["fechas"]]

    @pytest.mark.asyncio
    async def test_extract_cuantias(self, ner_instance):
        """Debe extraer cuantías del proceso."""
        text = "La cuantía del proceso es de $200.000.000 millones de pesos."
        result = await ner_instance.extract_entities(text)
        assert len(result["cuantias"]) > 0

    @pytest.mark.asyncio
    async def test_extract_tipo_proceso_tutela(self, ner_instance):
        """Debe detectar acciones de tutela."""
        text = "Se interpone acción de tutela contra la EPS Salud Vida."
        result = await ner_instance.extract_entities(text)
        tipos = [t["value"] for t in result["tipo_proceso"]]
        assert "TUTELA" in tipos

    @pytest.mark.asyncio
    async def test_extract_tipo_proceso_laboral(self, ner_instance):
        """Debe detectar procesos laborales."""
        text = "Se presenta demanda ordinaria laboral por despido injustificado."
        result = await ner_instance.extract_entities(text)
        tipos = [t["value"] for t in result["tipo_proceso"]]
        assert "LABORAL" in tipos

    @pytest.mark.asyncio
    async def test_extract_partes(self, ner_instance):
        """Debe extraer las partes del proceso."""
        text = "Actor: Juan Pérez López\nDemandado: María García Ruiz"
        result = await ner_instance.extract_entities(text)
        assert len(result["partes"]["actor"]) > 0
        assert len(result["partes"]["demandado"]) > 0

    @pytest.mark.parametrize("radicado", [
        "11001-31-03-001-2024-00001-00",
        "05001-31-03-001-2023-12345-01",
    ])
    @pytest.mark.asyncio
    async def test_extract_radicados_parametrized(self, ner_instance, radicado):
        """Debe extraer múltiples formatos de radicado."""
        text = f"Radicado: {radicado}"
        result = await ner_instance.extract_entities(text)
        assert len(result["radicados"]) > 0
        assert result["radicados"][0]["value"] in radicado

    @pytest.mark.asyncio
    async def test_empty_result_structure(self, ner_instance):
        """El resultado vacío debe tener todas las llaves esperadas."""
        result = await ner_instance.extract_entities("")
        assert "partes" in result
        assert "actor" in result["partes"]
        assert "demandado" in result["partes"]
        assert "terceros" in result["partes"]
        assert result["total_entities"] == 0


# ============================================
# Tests: BatchProcessor
# ============================================

class TestBatchProcessor:
    """Tests para el procesador batch."""

    @pytest.mark.asyncio
    async def test_process_file_not_found(self):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        from app.modules.extraction.batch_processor import BatchProcessor
        processor = BatchProcessor()

        with pytest.raises(FileNotFoundError):
            await processor.process_file("/ruta/inexistente.pdf")

    @pytest.mark.asyncio
    async def test_process_file_unsupported_extension(self):
        """Debe lanzar ValueError si la extensión no es soportada."""
        from app.modules.extraction.batch_processor import BatchProcessor
        processor = BatchProcessor()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                await processor.process_file(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_supported_extensions(self):
        """Debe soportar las extensiones esperadas."""
        from app.modules.extraction.batch_processor import BatchProcessor
        processor = BatchProcessor()

        expected = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
        assert set(processor.SUPPORTED_EXTENSIONS.keys()) == expected

    @pytest.mark.asyncio
    async def test_process_empty_batch(self):
        """Lista vacía debe retornar lista vacía."""
        from app.modules.extraction.batch_processor import BatchProcessor
        processor = BatchProcessor()

        results = await processor.process_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self):
        """Errores individuales no deben romper el batch."""
        from app.modules.extraction.batch_processor import BatchProcessor
        processor = BatchProcessor()

        results = await processor.process_batch(["/ruta/no/existe.pdf"])
        assert len(results) == 1
        assert results[0]["status"] == "error"


# ============================================
# Tests: Document Routes
# ============================================

class TestDocumentRoutes:
    """Tests para los endpoints de documentos."""

    def test_allowed_extensions(self):
        """Debe permitir las extensiones configuradas."""
        from app.api.routes.documents import ALLOWED_EXTENSIONS
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".png" in ALLOWED_EXTENSIONS
        assert ".jpg" in ALLOWED_EXTENSIONS

    def test_unsupported_extension_rejected(self):
        """Extensiones no soportadas deben ser rechazadas."""
        from app.api.routes.documents import ALLOWED_EXTENSIONS
        assert ".exe" not in ALLOWED_EXTENSIONS
        assert ".js" not in ALLOWED_EXTENSIONS
        assert ".html" not in ALLOWED_EXTENSIONS
