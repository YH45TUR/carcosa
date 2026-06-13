"""
Sistema Legal CO - Memoria Conversacional
Gestión de historial de conversaciones con el LLM.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class ConversationMemory:
    """
    Memoria conversacional para mantener contexto entre mensajes.
    Almacena historial en memoria con límite configurable.
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._sessions: Dict[int, List[Dict]] = {}  # session_id -> messages

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        module: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Agrega un mensaje al historial de la sesión."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "module": module,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })

        # Limitar tamaño del historial
        if len(self._sessions[session_id]) > self.max_history:
            self._sessions[session_id] = self._sessions[session_id][-self.max_history:]

    def get_history(
        self,
        session_id: int,
        last_n: Optional[int] = None
    ) -> List[Dict]:
        """Obtiene el historial de mensajes de una sesión."""
        messages = self._sessions.get(session_id, [])
        if last_n:
            return messages[-last_n:]
        return messages

    def get_context_for_llm(
        self,
        session_id: int,
        last_n: int = 10
    ) -> List[Dict]:
        """
        Obtiene el contexto formateado para el LLM.
        Retorna solo los campos role y content.
        """
        messages = self.get_history(session_id, last_n)
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    def clear_session(self, session_id: int) -> None:
        """Limpia el historial de una sesión."""
        self._sessions.pop(session_id, None)

    def has_session(self, session_id: int) -> bool:
        """Verifica si existe una sesión."""
        return session_id in self._sessions

    def get_session_count(self) -> int:
        """Obtiene el número de sesiones activas."""
        return len(self._sessions)


# Instancia global de memoria
conversation_memory = ConversationMemory()
