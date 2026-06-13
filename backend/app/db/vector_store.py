"""
Sistema Legal CO - Vector Store
ChromaDB para embeddings de jurisprudencia con estrategias de chunking.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from app.config import settings


class VectorStore:
    """
    Vector store con ChromaDB para RAG de jurisprudencia.
    Estrategia de chunking configurable.
    """
    
    def __init__(
        self,
        collection_name: str = "jurisprudencia",
        persist_directory: Optional[str] = None
    ):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Jurisprudencia colombiana - Altas Cortes"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Agrega documentos al vector store."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return ids
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Busca documentos similares."""
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un documento por ID."""
        try:
            result = self.collection.get(ids=[doc_id])
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else None
                }
        except Exception:
            pass
        return None
    
    def delete_collection(self) -> None:
        """Elimina la colección."""
        self.client.delete_collection(name=self.collection.name)
    
    def reset(self) -> None:
        """Resetea el vector store."""
        self.client.reset()


# ============================================
# ESTRATEGIAS DE CHUNKING
# ============================================

class ChunkingStrategy:
    """
    Estrategias de chunking para documentos legales.
    """
    
    @staticmethod
    def by_folio(text: str, folio_marker: str = "FOLIO") -> List[str]:
        """
        Chunking por folio.
        Ideal para expedientes físicos digitalizados.
        """
        chunks = []
        current_chunk = []
        
        for line in text.split("\n"):
            if folio_marker in line and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
            current_chunk.append(line)
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
    
    @staticmethod
    def by_section(text: str, section_headers: List[str]) -> List[str]:
        """
        Chunking por sección.
        Busca encabezados como 'HECHOS', 'FUNDAMENTOS', 'DECISIÓN', etc.
        """
        import re
        chunks = []
        pattern = "|".join(re.escape(h) for h in section_headers)
        parts = re.split(f"({pattern})", text, flags=re.IGNORECASE)
        
        current_section = ""
        for part in parts:
            if re.match(f"^({pattern})$", part, re.IGNORECASE):
                if current_section:
                    chunks.append(current_section.strip())
                current_section = part
            else:
                current_section += part
        
        if current_section:
            chunks.append(current_section.strip())
        
        return [c for c in chunks if c]
    
    @staticmethod
    def by_size(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Chunking por tamaño fijo con overlap.
        Útil para textos sin estructura clara.
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Ajustar para no cortar palabras
            if end < len(text):
                last_space = chunk.rfind(" ")
                if last_space > chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]


# Instancia global
vector_store = VectorStore()