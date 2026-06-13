"""
Sistema Legal CO - Chat
WebSocket chat con memoria conversacional y orquestación de módulos.
"""
import os

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.database import get_db
from app.core.security import get_current_user, decode_token
from app.models.user import User

# Rate limiter para chat
_is_testing = os.environ.get("TESTING", "").lower() == "true"
chat_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_chat_per_minute}/minute"] if not _is_testing else ["1000/minute"],
    enabled=not _is_testing
)

router = APIRouter()


# === SCHEMAS ===

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    case_id: Optional[int] = None
    module: Optional[str] = None  # drafting, extraction, audit, etc.


class ChatResponse(BaseModel):
    message: str
    module: str
    data: Optional[dict] = None


class ConnectionManager:
    """Gestor de conexiones WebSocket."""
    
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


# === WEBSOCKET ENDPOINT ===

@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str = ""
):
    """WebSocket para chat en tiempo real.
    
    Requiere token JWT como query parameter.
    Ejemplo: ws://localhost:8000/api/chat/ws?token=eyJhbGci...
    """
    # Validar token JWT
    if not token:
        await websocket.close(code=4001, reason="Token de autenticacion requerido")
        return
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=4001, reason="Token invalido")
            return
        # Nota: en produccion, obtener user_id real desde la DB
        # Por ahora usamos un hash simple del username
        user_id = abs(hash(username)) % 1000000
    except Exception:
        await websocket.close(code=4001, reason="Token expirado o invalido")
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Procesar mensaje
            response = await process_message(
                message_data.get("message", ""),
                message_data.get("case_id"),
                message_data.get("module")
            )
            
            await websocket.send_text(json.dumps(response))
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# === REST ENDPOINTS ===

@router.post("/message", response_model=ChatResponse)
@chat_limiter.limit(f"{settings.rate_limit_chat_per_minute}/minute")
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enviar mensaje de chat vía REST."""
    response = await process_message(
        chat_request.message,
        chat_request.case_id,
        chat_request.module
    )
    return response


@router.get("/history/{case_id}")
async def get_chat_history(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener historial de chat de un caso."""
    # Por implementar: guardar/recuperar mensajes de la DB
    return {"messages": []}


# === ORQUESTACIÓN ===

async def process_message(message: str, case_id: Optional[int], module: Optional[str]) -> dict:
    """
    Orquestador de intenciones.
    Detecta qué módulo debe manejar el mensaje.
    """
    from app.core.orchestrator import Router
    
    router_instance = Router()
    
    # Determinar módulo destino
    if module:
        intent_module = module
    else:
        intent_module = await router_instance.detect_intent(message)
    
    # Procesar según módulo
    result = await router_instance.route_message(
        message=message,
        module=intent_module,
        case_id=case_id
    )
    
    return {
        "message": result.get("response", ""),
        "module": intent_module,
        "data": result.get("data")
    }