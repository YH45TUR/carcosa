"""
Sistema Legal CO - Exportador PDF
Exporta documentos legales a PDF via LibreOffice headless.

Estrategia:
  1. Generar .docx con DOCXExporter (NTC 1486 aplicado)
  2. Convertir a PDF con `soffice --headless --convert-to pdf`
  3. LibreOffice preserva el formato exactamente, incluyendo
     fuentes Times New Roman instaladas en el Dockerfile.

WeasyPrint fue eliminado porque tenia problemas con Times New Roman
en Linux y soporte CSS limitado para layouts juridicos complejos.
"""
import os
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any


class PDFExporter:
    """
    Exportador de documentos legales a PDF usando LibreOffice headless.
    Aplica formato NTC 1486 via DOCXExporter y convierte a PDF.
    """

    # CSS incluido por compatibilidad (tests dependen de esta propiedad).
    # El PDF real se genera via LibreOffice, no con este CSS.
    LEGAL_CSS = """
    @page {
        size: letter;
        margin-top: 3cm;
        margin-bottom: 3cm;
        margin-left: 4cm;
        margin-right: 2cm;

        @bottom-center {
            content: counter(page);
            font-family: 'Times New Roman', Times, serif;
            font-size: 10pt;
        }
    }

    body {
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #000000;
        text-align: justify;
    }

    .section-title {
        text-align: center;
        font-weight: bold;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        text-indent: 0;
        text-transform: uppercase;
    }

    .list-item {
        margin-left: 1cm;
        text-indent: -0.5cm;
    }

    .signature {
        margin-top: 4em;
        text-align: center;
        text-indent: 0;
    }

    p.empty {
        text-indent: 0;
        height: 1.5em;
    }
    """

    def __init__(self):
        self._soffice_available = shutil.which("soffice") is not None

    async def export(
        self,
        content: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Exporta contenido de texto a PDF con formato legal colombiano.

        Flujo:
          texto -> .docx (NTC 1486 via DOCXExporter) -> PDF (soffice headless)

        Args:
            content: Texto del documento legal
            output_path: Ruta donde guardar el PDF
            metadata: Metadatos (titulo, autor, etc.)

        Returns:
            Ruta al archivo PDF generado

        Raises:
            RuntimeError: Si LibreOffice no esta instalado o falla la conversion
        """
        if not self._soffice_available:
            raise RuntimeError(
                "LibreOffice no esta instalado. "
                "Asegurate de usar el Dockerfile actualizado con libreoffice-writer."
            )

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Paso 1: generar .docx temporal con formato NTC 1486
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            tmp_docx_path = tmp_docx.name

        try:
            from app.modules.drafting.exporter_docx import DOCXExporter
            docx_exporter = DOCXExporter()
            await docx_exporter.export(content, tmp_docx_path, metadata)

            # Paso 2: convertir .docx a PDF con LibreOffice headless
            tmp_dir = os.path.dirname(tmp_docx_path)
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmp_dir,
                    tmp_docx_path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice fallo al convertir a PDF: {result.stderr[:300]}"
                )

            # LibreOffice genera el PDF en el mismo directorio con el mismo nombre
            tmp_pdf_path = tmp_docx_path.replace(".docx", ".pdf")
            if not os.path.exists(tmp_pdf_path):
                raise RuntimeError("LibreOffice no genero el archivo PDF esperado")

            # Paso 3: mover PDF a la ruta de salida final
            shutil.move(tmp_pdf_path, output_path)

        finally:
            # Limpiar archivo .docx temporal
            if os.path.exists(tmp_docx_path):
                os.unlink(tmp_docx_path)

        return output_path

    def _text_to_html(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Convierte texto plano a HTML estructurado (usado en tests y previsualizacion)."""
        html_parts = ['<html><head><meta charset="utf-8">']
        html_parts.append(
            f'<title>{metadata.get("title", "Documento Legal") if metadata else "Documento Legal"}</title>'
        )
        html_parts.append(f'<style>{self.LEGAL_CSS}</style>')
        html_parts.append('</head><body>')

        for line in content.split('\n'):
            stripped = line.strip()

            if not stripped:
                html_parts.append('<p class="empty">&nbsp;</p>')
                continue

            if stripped.isupper() and len(stripped) > 3:
                html_parts.append(f'<div class="section-title">{self._escape_html(stripped)}</div>')
                continue

            if (stripped[0].isdigit() and '. ' in stripped[:5]) or \
               (len(stripped) > 2 and stripped[0].isalpha() and ') ' in stripped[:5]):
                html_parts.append(f'<p class="list-item">{self._escape_html(stripped)}</p>')
                continue

            html_parts.append(f'<p>{self._escape_html(stripped)}</p>')

        html_parts.append('</body></html>')
        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escapa caracteres HTML."""
        return (
            text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;')
        )
