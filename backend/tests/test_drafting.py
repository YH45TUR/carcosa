"""
Sistema Legal CO - Tests de Redacción Jurídica
Pruebas unitarias para el módulo de drafting usando pytest.

Referencia: skills/pytest/SKILL.md
"""
import pytest
import os
import json
import tempfile
from datetime import datetime


@pytest.fixture
def generator():
    """Instancia del DraftingGenerator."""
    from app.modules.drafting.generator import DraftingGenerator
    return DraftingGenerator()


@pytest.fixture
def docx_exporter():
    """Instancia del DOCXExporter."""
    from app.modules.drafting.exporter_docx import DOCXExporter
    return DOCXExporter()


@pytest.fixture
def pdf_exporter():
    """Instancia del PDFExporter."""
    from app.modules.drafting.exporter_pdf import PDFExporter
    return PDFExporter()


@pytest.fixture
def sample_content():
    """Contenido de ejemplo para exportar."""
    return """DEMANDA CIVIL

Bogotá D.C., 15 de marzo de 2024

Señor
JUEZ CIVIL DEL CIRCUITO DE BOGOTÁ (REPARTO)
E. S. D.

I. PRETENSIONES

1. Que se declare civilmente responsable al demandado.

2. Que se condene al demandado al pago de perjuicios.

II. HECHOS

1. El día 15 de enero de 2024 ocurrieron los hechos.

2. El demandante sufrió perjuicios valorados en $100.000.000.

Atentamente,

Carlos Martínez
Abogado
T.P. No. 123.456"""


# ============================================
# Tests: DraftingGenerator
# ============================================

class TestDraftingGenerator:
    """Tests para el generador de documentos."""

    @pytest.mark.asyncio
    async def test_detect_document_type_demanda(self, generator):
        """Debe detectar demanda en el texto."""
        doc_type = await generator._detect_document_type(
            "Necesito una demanda civil por incumplimiento de contrato"
        )
        assert doc_type == "demanda"

    @pytest.mark.asyncio
    async def test_detect_document_type_tutela(self, generator):
        """Debe detectar acción de tutela."""
        doc_type = await generator._detect_document_type(
            "Presentar acción de tutela por violación del derecho a la salud"
        )
        assert doc_type == "tutela"

    @pytest.mark.asyncio
    async def test_detect_document_type_recurso(self, generator):
        """Debe detectar recurso de apelación."""
        doc_type = await generator._detect_document_type(
            "Apelar la sentencia del juzgado"
        )
        assert doc_type == "recurso"

    @pytest.mark.asyncio
    async def test_detect_document_type_peticion(self, generator):
        """Debe detectar derecho de petición."""
        doc_type = await generator._detect_document_type(
            "Derecho de petición para solicitar información"
        )
        assert doc_type == "derecho_peticion"

    @pytest.mark.asyncio
    async def test_detect_default_demanda(self, generator):
        """Mensaje sin keywords claras debe default a demanda."""
        doc_type = await generator._detect_document_type("Ayuda con un documento legal")
        assert doc_type == "demanda"

    @pytest.mark.asyncio
    async def test_unsupported_document_type(self, generator):
        """Tipo no soportado debe retornar error."""
        result = await generator.generate(
            message="test",
            document_type="test_invalido",
        )
        assert not result["success"]

    @pytest.mark.asyncio
    async def test_generate_mock_data_tutela(self, generator):
        """Los datos mock para tutela deben incluir campos específicos."""
        data = generator._generate_mock_data("tutela médica", "tutela")
        assert "derechos_vulnerados" in data
        assert "fundamentos_accion" in data
        assert len(data["derechos_vulnerados"]) > 0

    @pytest.mark.asyncio
    async def test_generate_mock_data_recurso(self, generator):
        """Los datos mock para recurso deben incluir campos específicos."""
        data = generator._generate_mock_data("apelar sentencia", "recurso")
        assert "cargos_inconformidad" in data
        assert "tribunal_superior" in data
        assert "sustentacion" in data

    @pytest.mark.asyncio
    async def test_generate_mock_data_peticion(self, generator):
        """Los datos mock para derecho de petición deben incluir campos específicos."""
        data = generator._generate_mock_data("solicitar información", "derecho_peticion")
        assert "solicitudes" in data
        assert "autoridad_destinataria" in data
        assert "fundamentos_juridicos" in data

    @pytest.mark.asyncio
    async def test_generate_from_data_demanda(self, generator):
        """generate_from_data debe producir un documento con demanda."""
        data = {
            "demandante": "Juan Pérez",
            "demandado": "María García",
            "hechos": ["Hecho 1", "Hecho 2"],
            "pretensiones": ["Pretensión 1"],
        }
        result = await generator.generate_from_data("demanda", data)
        assert "content" in result
        assert "Juan Pérez" in result["content"]
        assert "María García" in result["content"]
        assert result["document_type"] == "demanda"
        assert result["word_count"] > 0

    @pytest.mark.asyncio
    async def test_generate_from_data_invalid_type(self, generator):
        """Tipo inválido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            await generator.generate_from_data("tipo_invalido", {})

    @pytest.mark.asyncio
    async def test_generate_from_data_missing_fields(self, generator):
        """Campos faltantes deben usar defaults."""
        result = await generator.generate_from_data("tutela", {})
        assert "content" in result
        assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_document_types_completeness(self, generator):
        """Todos los tipos de documento deben tener template y campos requeridos."""
        for doc_type, config in generator.DOCUMENT_TYPES.items():
            assert "template" in config
            assert config["template"].endswith(".j2")
            assert "required_fields" in config
            assert len(config["required_fields"]) > 0

    @pytest.mark.asyncio
    async def test_generate_mock_data_with_case(self, generator):
        """Datos del caso deben sobrescribir datos mock."""
        case_data = {"demandante": "Cliente Real", "radicado": "2000-01"}
        data = generator._generate_mock_data("test", "demanda", case_data)
        assert data["demandante"] == "Cliente Real"
        assert data["radicado"] == "2000-01"


# ============================================
# Tests: DOCXExporter
# ============================================

class TestDOCXExporter:
    """Tests para el exportador DOCX."""

    @pytest.mark.asyncio
    async def test_export_creates_file(self, docx_exporter, sample_content):
        """Exportar debe crear un archivo .docx."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = f.name

        try:
            result = await docx_exporter.export(sample_content, output_path)
            assert os.path.exists(result)
            assert result == output_path
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    async def test_export_with_metadata(self, docx_exporter, sample_content):
        """Exportar con metadatos debe incluirlos."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = f.name

        try:
            result = await docx_exporter.export(
                sample_content,
                output_path,
                metadata={"title": "Test", "author": "Tester"},
            )
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    async def test_export_with_template_types(self, docx_exporter, sample_content):
        """Exportar con diferentes tipos de documento debe funcionar."""
        for doc_type in ["demanda", "tutela", "recurso", "derecho_peticion"]:
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                output_path = f.name

            try:
                result = await docx_exporter.export_with_template(
                    sample_content, output_path, doc_type
                )
                assert os.path.exists(result)
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)


# ============================================
# Tests: PDFExporter
# ============================================

class TestPDFExporter:
    """Tests para el exportador PDF."""

    @pytest.mark.asyncio
    async def test_text_to_html_structure(self, pdf_exporter, sample_content):
        """La conversión a HTML debe mantener la estructura."""
        html = pdf_exporter._text_to_html(sample_content)
        assert "<html>" in html
        assert "</html>" in html
        assert "<style>" in html
        assert "section-title" in html
        assert "DEMANDA CIVIL" in html

    @pytest.mark.asyncio
    async def test_escape_html(self, pdf_exporter):
        """Los caracteres especiales deben escaparse."""
        escaped = pdf_exporter._escape_html("Texto con < & > comillas \"'")
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&amp;" in escaped
        assert "&quot;" in escaped

    @pytest.mark.asyncio
    async def test_text_to_html_empty_lines(self, pdf_exporter):
        """Líneas vacías deben convertirse a párrafos vacíos."""
        html = pdf_exporter._text_to_html("Línea 1\n\nLínea 2")
        assert 'class="empty"' in html

    @pytest.mark.asyncio
    async def test_text_to_html_list_items(self, pdf_exporter):
        """Items con numeración deben tener clase list-item."""
        html = pdf_exporter._text_to_html("1. Item uno\n2. Item dos")
        assert 'class="list-item"' in html

    @pytest.mark.asyncio
    async def test_text_to_html_sections(self, pdf_exporter):
        """Secciones en mayúsculas deben tener clase section-title."""
        html = pdf_exporter._text_to_html("HECHOS\n\nTexto de hechos")
        assert 'class="section-title"' in html

    @pytest.mark.asyncio
    async def test_legal_css_structure(self, pdf_exporter):
        """El CSS debe incluir reglas para todos los elementos legales."""
        css = pdf_exporter.LEGAL_CSS
        assert "@page" in css
        assert "Times New Roman" in css
        assert "section-title" in css
        assert "list-item" in css
        assert "signature" in css

    @pytest.mark.asyncio
    async def test_text_to_html_includes_metadata(self, pdf_exporter, sample_content):
        """El HTML debe incluir metadatos si se proporcionan."""
        html = pdf_exporter._text_to_html(sample_content, {"title": "Documento de Prueba"})
        assert "Documento de Prueba" in html


# ============================================
# Tests: Export Routes
# ============================================

class TestExportRoutes:
    """Tests para los endpoints de exportación."""

    def test_export_dir_configured(self):
        """El directorio de exportación debe estar configurado."""
        from app.api.routes.export import EXPORT_DIR
        assert EXPORT_DIR is not None
        assert "exports" in EXPORT_DIR

    @pytest.mark.skip(reason="Requiere integración con FastAPI TestClient")
    def test_generate_without_content(self):
        """Generar sin contenido debe retornar error."""
        pass
