"""
Sistema Legal CO - Exportador PDF
Exporta documentos legales a PDF con WeasyPrint y estilos CSS.
Formato equivalente a NTC 1486 para impresión profesional.
"""
from typing import Optional, Dict, Any
import os


class PDFExporter:
    """
    Exportador de documentos legales a PDF usando WeasyPrint.
    Aplica estilos CSS equivalentes a NTC 1486.
    """

    # Estilos CSS para documentos legales colombianos
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

    h1, h2, h3, h4 {
        font-family: 'Times New Roman', Times, serif;
        font-weight: bold;
        text-align: center;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        font-size: 12pt;
    }

    p {
        margin: 0;
        padding: 0;
        text-indent: 1cm;
    }

    p.empty {
        text-indent: 0;
        height: 1.5em;
    }

    .signature {
        margin-top: 4em;
        text-align: center;
        text-indent: 0;
    }

    .signature-name {
        font-weight: bold;
        margin-top: 0.5em;
    }

    .header {
        text-align: right;
        margin-bottom: 2em;
        text-indent: 0;
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

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
    }

    table td, table th {
        border: 1px solid #000;
        padding: 8px;
        font-size: 11pt;
    }

    table th {
        font-weight: bold;
        background-color: #f0f0f0;
    }
    """

    def __init__(self):
        self._available = False
        try:
            from weasyprint import HTML
            self._HTML = HTML
            self._available = True
        except ImportError:
            pass

    async def export(
        self,
        content: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Exporta contenido de texto a PDF con formato legal colombiano.

        Args:
            content: Texto del documento legal
            output_path: Ruta donde guardar el PDF
            metadata: Metadatos (título, autor, etc.)

        Returns:
            Ruta al archivo generado
        """
        if not self._available:
            raise ImportError("WeasyPrint no está instalado. pip install weasyprint")

        html_content = self._text_to_html(content, metadata)
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        self._HTML(string=html_content).write_pdf(output_path)

        return output_path

    def _text_to_html(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Convierte texto plano a HTML con estructura legal."""
        html_parts = ['<html><head><meta charset="utf-8">']
        html_parts.append(f'<title>{metadata.get("title", "Documento Legal") if metadata else "Documento Legal"}</title>')
        html_parts.append(f'<style>{self.LEGAL_CSS}</style>')
        html_parts.append('</head><body>')

        lines = content.split('\n')
        in_list = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                html_parts.append('<p class="empty">&nbsp;</p>')
                in_list = False
                continue

            # Secciones en mayúsculas
            if stripped.isupper() and len(stripped) > 3:
                html_parts.append(f'<div class="section-title">{self._escape_html(stripped)}</div>')
                in_list = False
                continue

            # Numeración legal
            if (stripped[0].isdigit() and '. ' in stripped[:5]) or \
               (len(stripped) > 2 and stripped[0].isalpha() and ') ' in stripped[:5]):
                html_parts.append(f'<p class="list-item">{self._escape_html(stripped)}</p>')
                in_list = True
                continue

            # Texto normal con justificación
            html_parts.append(f'<p>{self._escape_html(stripped)}</p>')
            in_list = False

        # Firma simulada si no hay
        html_parts.append('</body></html>')

        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escapa caracteres HTML."""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;'))
