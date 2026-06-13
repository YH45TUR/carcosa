"""
Sistema Legal CO - PDF Parser
Extracción de texto y tablas de documentos PDF usando PyMuPDF y pdfplumber.
"""
from typing import Optional, List, Dict, Any
import os
import json


class PDFParser:
    """
    Parser de documentos PDF con soporte para:
    - Texto plano con PyMuPDF (rápido)
    - Tablas con pdfplumber (preciso)
    - Metadatos del documento
    """

    def __init__(self):
        self._fitz_available = False
        self._plumber_available = False

        try:
            import fitz
            self._fitz = fitz
            self._fitz_available = True
        except ImportError:
            pass

        try:
            import pdfplumber
            self._pdfplumber = pdfplumber
            self._plumber_available = True
        except ImportError:
            pass

    async def extract_text(self, file_path: str) -> str:
        """
        Extrae todo el texto de un PDF.

        Usa PyMuPDF por velocidad, con fallback a pdfplumber.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        if self._fitz_available:
            return await self._extract_with_fitz(file_path)

        if self._plumber_available:
            return await self._extract_with_plumber(file_path)

        raise ImportError(
            "No hay motor PDF disponible. Instala: pip install pymupdf pdfplumber"
        )

    async def extract_pages(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extrae texto página por página con metadatos.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        pages = []

        if self._fitz_available:
            doc = self._fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages.append({
                    "page": page_num + 1,
                    "text": text.strip(),
                    "char_count": len(text),
                })
            doc.close()
            return pages

        if self._plumber_available:
            with self._pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append({
                        "page": page_num + 1,
                        "text": text.strip(),
                        "char_count": len(text),
                    })
            return pages

        raise ImportError("No hay motor PDF disponible")

    async def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extrae tablas del PDF (solo con pdfplumber).
        """
        if not self._plumber_available:
            return []

        tables = []
        with self._pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    tables.append({
                        "page": page_num + 1,
                        "table_index": table_idx,
                        "headers": table[0] if table else [],
                        "rows": table[1:] if len(table) > 1 else [],
                        "row_count": len(table) - 1 if len(table) > 1 else 0,
                    })
        return tables

    async def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene metadatos del PDF.
        """
        metadata = {
            "filename": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "page_count": 0,
            "author": None,
            "title": None,
            "subject": None,
        }

        if self._fitz_available:
            doc = self._fitz.open(file_path)
            metadata["page_count"] = len(doc)
            doc_meta = doc.metadata
            metadata["author"] = doc_meta.get("author")
            metadata["title"] = doc_meta.get("title")
            metadata["subject"] = doc_meta.get("subject")
            doc.close()

        elif self._plumber_available:
            with self._pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)

        return metadata

    async def _extract_with_fitz(self, file_path: str) -> str:
        """Extracción rápida con PyMuPDF."""
        doc = self._fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n\n".join(text_parts)

    async def _extract_with_plumber(self, file_path: str) -> str:
        """Extracción de respaldo con pdfplumber."""
        text_parts = []
        with self._pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
