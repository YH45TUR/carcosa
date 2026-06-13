"""
Sistema Legal CO - OCR Engine
Reconocimiento óptico de caracteres para documentos escaneados e imágenes.
Usa PaddleOCR optimizado para español.
"""
from typing import Optional, List, Dict, Any, Tuple
import os
import tempfile


class OCREngine:
    """
    Motor OCR para imágenes y PDFs escaneados.

    Características:
    - Optimizado para español
    - Soporta PDFs escaneados (convierte a imágenes primero)
    - Detección de región de texto
    """

    def __init__(self):
        self._paddle_available = False
        self._ocr_instance = None

        try:
            from paddleocr import PaddleOCR
            self._PaddleOCR = PaddleOCR
            self._paddle_available = True
        except ImportError:
            pass

    def _get_ocr(self):
        """Obtiene o crea la instancia de PaddleOCR."""
        if self._ocr_instance is None and self._paddle_available:
            self._ocr_instance = self._PaddleOCR(
                use_angle_cls=True,
                lang='es',
                use_gpu=False,
                show_log=False,
            )
        return self._ocr_instance

    async def extract_text_from_image(self, image_path: str) -> str:
        """
        Extrae texto de una imagen usando OCR.

        Args:
            image_path: Ruta a la imagen (PNG, JPG, etc.)

        Returns:
            Texto extraído
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
        if not self._paddle_available:
            raise ImportError("PaddleOCR no está instalado. pip install paddleocr paddlepaddle")

        ocr = self._get_ocr()
        result = ocr.ocr(image_path, cls=True)

        return self._format_ocr_result(result)

    async def extract_text_from_pdf_page(
        self,
        pdf_path: str,
        page_number: int,
        dpi: int = 300
    ) -> str:
        """
        Extrae texto de una página específica de un PDF escaneado.

        Convierte la página a imagen y aplica OCR.

        Args:
            pdf_path: Ruta al PDF
            page_number: Número de página (1-indexed)
            dpi: Resolución para la conversión

        Returns:
            Texto extraído
        """
        if not self._paddle_available:
            raise ImportError("PaddleOCR no está instalado")

        # Convertir página PDF a imagen
        image_path = await self._pdf_page_to_image(pdf_path, page_number, dpi)
        if not image_path:
            return ""

        try:
            text = await self.extract_text_from_image(image_path)
            return text
        finally:
            # Limpiar archivo temporal
            try:
                os.remove(image_path)
            except OSError:
                pass

    async def extract_text_from_scanned_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto de todas las páginas de un PDF escaneado.

        Args:
            pdf_path: Ruta al PDF escaneado

        Returns:
            Texto completo extraído
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Primero intentar extraer con PyMuPDF (por si tiene texto)
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text_parts = []
            for page in doc:
                page_text = page.get_text().strip()
                if page_text:
                    text_parts.append(page_text)
            doc.close()

            # Si tiene suficiente texto, devolverlo directamente
            total_text = " ".join(text_parts)
            if len(total_text) > 100:
                return total_text
        except ImportError:
            pass

        # Si no hay texto (PDF escaneado), usar OCR
        if not self._paddle_available:
            return "PDF escaneado detectado. Instala PaddleOCR para procesarlo."

        # Obtener número de páginas
        try:
            import fitz
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except ImportError:
            total_pages = 1

        text_parts = []
        for page_num in range(1, total_pages + 1):
            page_text = await self.extract_text_from_pdf_page(pdf_path, page_num)
            if page_text:
                text_parts.append(f"[Página {page_num}]\n{page_text}")

        return "\n\n".join(text_parts)

    def _format_ocr_result(self, result: List) -> str:
        """
        Formatea el resultado de PaddleOCR a texto plano.
        """
        if not result or not result[0]:
            return ""

        text_parts = []
        for line in result[0]:
            if len(line) >= 2:
                text = line[1][0]  # (text, confidence)
                text_parts.append(text)

        return "\n".join(text_parts)

    async def _pdf_page_to_image(
        self,
        pdf_path: str,
        page_number: int,
        dpi: int = 300
    ) -> Optional[str]:
        """
        Convierte una página de PDF a imagen temporal.

        Returns:
            Ruta a la imagen temporal o None si falla
        """
        try:
            import fitz
            doc = fitz.open(pdf_path)
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return None

            page = doc[page_number - 1]
            zoom = dpi / 72  # 72 es el DPI base de PDF
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Guardar a archivo temporal
            fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            pix.save(temp_path)

            doc.close()
            return temp_path

        except ImportError:
            return None
        except Exception:
            return None
