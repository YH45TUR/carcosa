"""
Sistema Legal CO - RAG para Jurisprudencia
Búsqueda semántica de jurisprudencia usando ChromaDB.

Reutiliza la estrategia de chunking del Módulo 3 (vector_store.py)
y añade funcionalidades específicas para jurisprudencia.
"""
from typing import Optional, Dict, Any, List
import os
import json
from datetime import datetime

from app.config import settings


class JurisprudenceRAG:
    """
    Sistema RAG para jurisprudencia colombiana.

    Características:
    - Embeddings de sentencias en ChromaDB
    - Búsqueda semántica con filtros por corte, año, tipo
    - Auto-citación en formato Colombia
    """

    COLECCIONES = {
        "corte_constitucional": "Sentencias Corte Constitucional",
        "corte_suprema": "Sentencias Corte Suprema de Justicia",
        "consejo_estado": "Sentencias Consejo de Estado",
        "suin_juriscol": "Normativa SUIN-JURISCOL",
    }

    def __init__(self):
        self._chroma_available = False
        self._vector_store = None

        try:
            from app.db.vector_store import VectorStore, ChunkingStrategy
            self._VectorStore = VectorStore
            self._ChunkingStrategy = ChunkingStrategy
            self._chroma_available = True
        except ImportError:
            pass

    async def search(
        self,
        query: str,
        fuente: str = "corte_constitucional",
        n_results: int = 5,
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Búsqueda semántica de jurisprudencia.

        Args:
            query: Consulta en lenguaje natural
            fuente: Fuente específica o "todas"
            n_results: Número de resultados
            filters: Filtros adicionales (año, tipo, etc.)

        Returns:
            Resultados con contexto y citas
        """
        if not self._chroma_available:
            return await self._fallback_search(query, fuente, n_results)

        vs = self._VectorStore()

        if fuente != "todas":
            vs.collection = vs.client.get_or_create_collection(
                name=fuente,
                metadata={"description": self.COLECCIONES.get(fuente, fuente)}
            )

        # Construir filtros
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                if value:
                    where[key] = value

        try:
            results = vs.query(
                query_text=query,
                n_results=n_results,
                where=where,
            )

            formatted = self._format_results(results, fuente)
            return {
                "success": True,
                "response": formatted,
                "data": {
                    "source": fuente,
                    "results": results,
                    "total": len(results.get("ids", [[]])[0]) if results.get("ids") else 0,
                },
            }

        except Exception as e:
            return await self._fallback_search(query, fuente, n_results)

    async def add_sentencia(
        self,
        texto: str,
        metadata: Dict[str, Any],
        fuente: str = "corte_constitucional",
    ) -> str:
        """
        Agrega una sentencia al vector store.

        Args:
            texto: Texto completo de la sentencia
            metadata: Metadatos (corte, año, tipo, radicado, etc.)
            fuente: Colección destino

        Returns:
            ID del documento agregado
        """
        if not self._chroma_available:
            return ""

        vs = self._VectorStore(collection_name=fuente)
        chunks = self._ChunkingStrategy.by_section(
            texto,
            section_headers=["HECHOS", "CONSIDERACIONES", "DECISIÓN", "FALLO",
                            "ANTECEDENTES", "PARTES", "RESUELVE"]
        )

        if not chunks:
            chunks = self._ChunkingStrategy.by_size(texto)

        metadatas = [{**metadata, "chunk": i} for i in range(len(chunks))]
        ids = [f"{fuente}_{metadata.get('radicado', datetime.now().timestamp())}_{i}"
               for i in range(len(chunks))]

        vs.add_documents(chunks, metadatas, ids)
        return ids[0] if ids else ""

    async def format_citation(self, sentencia: Dict[str, Any]) -> str:
        """
        Genera cita en formato Colombia para una sentencia.

        Formatos:
        - Corte Constitucional: T-123/24, C-456/24
        - Corte Suprema: SC1234-2024, SP5678-2024
        - Consejo de Estado: CE-12345-2024
        """
        tipo = sentencia.get("tipo", "sentencia")
        corte = sentencia.get("corte", "")
        numero = sentencia.get("numero", "")
        ano = sentencia.get("año", datetime.now().year)
        magistrado = sentencia.get("magistrado_ponente", "")

        if "constitucional" in corte.lower():
            return f"{tipo.upper()}-{numero}/{str(ano)[-2:]}"
        elif "suprema" in corte.lower():
            return f"SC{numero}-{ano}"
        elif "estado" in corte.lower():
            return f"CE-{numero}-{ano}"
        else:
            return f"{corte}, {tipo} No. {numero} de {ano}"

    def _format_results(self, results: Dict[str, Any], fuente: str) -> str:
        """Formatea resultados de ChromaDB."""
        if not results.get("ids") or not results["ids"][0]:
            return f"No se encontraron resultados semánticos en {self.COLECCIONES.get(fuente, fuente)}."

        lines = [
            f"🔍 Búsqueda semántica en {self.COLECCIONES.get(fuente, fuente)}",
            f"",
        ]

        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            doc_text = results["documents"][0][i] if results.get("documents") else ""
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

            titulo = metadata.get("titulo", f"Resultado {i + 1}")
            lines.append(f"{i + 1}. {titulo}")
            if doc_text:
                lines.append(f"   {doc_text[:300]}...")
            if metadata.get("fecha"):
                lines.append(f"   📅 {metadata['fecha']}")
            lines.append("")

        return "\n".join(lines)

    async def _fallback_search(
        self,
        query: str,
        fuente: str,
        n_results: int,
    ) -> Dict[str, Any]:
        """
        Fallback cuando ChromaDB no está disponible.
        """
        from app.modules.jurisprudence.searcher import JurisprudenceSearcher

        searcher = JurisprudenceSearcher()
        result = await searcher.search(
            query=query,
            fuente_id=fuente,
            max_results=n_results,
        )

        return {
            "success": result["success"],
            "response": result["response"],
            "data": {
                "source": fuente,
                "mode": "fallback_web_search",
                "results": result.get("data", {}).get("results", []),
                "total": result.get("data", {}).get("total", 0),
            },
        }
