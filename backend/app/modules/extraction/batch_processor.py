"""
Sistema Legal CO - Batch Processor
Procesamiento de múltiples archivos de un caso con pipeline completo:
PDF/DOCX/Imagen → Texto → NER → Chunking → Vector Store.
"""
from typing import List, Dict, Any, Optional, Callable
import os
import json
import asyncio
from datetime import datetime

from app.config import settings


class BatchProcessor:
    """
    Procesa múltiples archivos pertenecientes a un mismo caso.

    Pipeline:
    1. Detectar tipo de archivo y elegir parser
    2. Extraer texto (PDF/DOCX/OCR según corresponda)
    3. Extraer entidades legales (NER)
    4. Aplicar chunking para RAG
    5. Almacenar en vector store (opcional)
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".tiff": "image",
        ".tif": "image",
    }

    def __init__(self):
        self._pdf_parser = None
        self._docx_parser = None
        self._ocr_engine = None
        self._ner = None
        self._vector_store = None

    def _get_pdf_parser(self):
        if self._pdf_parser is None:
            from app.modules.extraction.pdf_parser import PDFParser
            self._pdf_parser = PDFParser()
        return self._pdf_parser

    def _get_docx_parser(self):
        if self._docx_parser is None:
            from app.modules.extraction.docx_parser import DOCXParser
            self._docx_parser = DOCXParser()
        return self._docx_parser

    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            from app.modules.extraction.ocr_engine import OCREngine
            self._ocr_engine = OCREngine()
        return self._ocr_engine

    def _get_ner(self):
        if self._ner is None:
            from app.modules.extraction.ner import LegalNER
            self._ner = LegalNER()
        return self._ner

    def _get_vector_store(self):
        if self._vector_store is None:
            from app.db.vector_store import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store

    async def process_file(
        self,
        file_path: str,
        chunk_strategy: str = "by_size",
        enable_ner: bool = True,
        enable_vector_store: bool = False
    ) -> Dict[str, Any]:
        """
        Procesa un solo archivo con todo el pipeline.

        Args:
            file_path: Ruta al archivo
            chunk_strategy: Estrategia de chunking (by_size, by_section, by_folio)
            enable_ner: Si se debe ejecutar NER
            enable_vector_store: Si se debe almacenar en vector store

        Returns:
            Resultado del procesamiento con texto, entidades y chunks
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        file_type = self.SUPPORTED_EXTENSIONS.get(ext)

        if not file_type:
            raise ValueError(f"Tipo de archivo no soportado: {ext}")

        result = {
            "filename": os.path.basename(file_path),
            "file_type": file_type,
            "file_size": os.path.getsize(file_path),
            "text": "",
            "entities": None,
            "chunks": [],
            "status": "processing",
            "error": None,
        }

        try:
            # Paso 1: Extraer texto según tipo
            if file_type == "pdf":
                text = await self._process_pdf(file_path)
            elif file_type == "docx":
                text = await self._process_docx(file_path)
            elif file_type == "image":
                text = await self._process_image(file_path)
            else:
                raise ValueError(f"Tipo no soportado: {file_type}")

            result["text"] = text

            if not text.strip():
                result["status"] = "no_text"
                return result

            # Paso 2: NER (opcional)
            if enable_ner:
                ner = self._get_ner()
                entities = await ner.extract_entities(text)
                result["entities"] = entities

            # Paso 3: Chunking
            chunks = await self._apply_chunking(text, chunk_strategy)
            result["chunks"] = chunks

            # Paso 4: Vector store (opcional)
            if enable_vector_store and chunks:
                await self._store_chunks(chunks, file_path)

            result["status"] = "completed"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def process_batch(
        self,
        file_paths: List[str],
        chunk_strategy: str = "by_size",
        enable_ner: bool = True,
        enable_vector_store: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa múltiples archivos en paralelo.

        Args:
            file_paths: Lista de rutas de archivos
            chunk_strategy: Estrategia de chunking
            enable_ner: Ejecutar NER
            enable_vector_store: Almacenar en vector store
            progress_callback: Callback para reportar progreso

        Returns:
            Lista de resultados por archivo
        """
        total = len(file_paths)
        results = []

        # Procesar en lotes de 3 para no saturar recursos
        batch_size = 3
        for i in range(0, total, batch_size):
            batch = file_paths[i:i + batch_size]
            tasks = [
                self.process_file(f, chunk_strategy, enable_ner, enable_vector_store)
                for f in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, res in enumerate(batch_results):
                if isinstance(res, Exception):
                    results.append({
                        "filename": os.path.basename(batch[idx]),
                        "status": "error",
                        "error": str(res),
                    })
                else:
                    results.append(res)

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

        return results

    async def _process_pdf(self, file_path: str) -> str:
        """Extrae texto de PDF, con fallback a OCR si está escaneado."""
        parser = self._get_pdf_parser()
        text = await parser.extract_text(file_path)

        # Si el texto es muy corto, podría ser escaneado → OCR
        if len(text.strip()) < 100:
            ocr = self._get_ocr_engine()
            ocr_text = await ocr.extract_text_from_scanned_pdf(file_path)
            if ocr_text and len(ocr_text) > len(text):
                text = ocr_text

        return text

    async def _process_docx(self, file_path: str) -> str:
        """Extrae texto de DOCX."""
        parser = self._get_docx_parser()
        return await parser.extract_text(file_path)

    async def _process_image(self, file_path: str) -> str:
        """Extrae texto de imagen vía OCR."""
        ocr = self._get_ocr_engine()
        return await ocr.extract_text_from_image(file_path)

    async def _apply_chunking(self, text: str, strategy: str) -> List[str]:
        """Aplica la estrategia de chunking configurada."""
        from app.db.vector_store import ChunkingStrategy

        if strategy == "by_folio":
            return ChunkingStrategy.by_folio(text)
        elif strategy == "by_section":
            section_headers = [
                "HECHOS", "FUNDAMENTOS", "DECISIÓN", "CONSIDERACIONES",
                "PARTES", "ANTECEDENTES", "PRETENSIONES", "PRUEBAS",
                "NOTIFICACIONES", "COSTAS", "RESUELVE", "FALLO",
                "DEMANDA", "CONTESTACIÓN", "RECURSO", "ALEGATOS",
            ]
            return ChunkingStrategy.by_section(text, section_headers)
        else:
            return ChunkingStrategy.by_size(text)

    async def _store_chunks(self, chunks: List[str], file_path: str) -> None:
        """Almacena chunks en el vector store."""
        vs = self._get_vector_store()
        doc_id = f"doc_{os.path.basename(file_path)}_{datetime.now().timestamp()}"
        metadatas = [{"source": os.path.basename(file_path)} for _ in chunks]
        vs.add_documents(chunks, metadatas, [f"{doc_id}_{i}" for i in range(len(chunks))])
