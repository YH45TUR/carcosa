"""
Sistema Legal CO - Chat
WebSocket chat con memoria conversacional y orquestación de módulos.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User

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
    token: str
):
    """WebSocket para chat en tiempo real."""
    # Nota: En producción, validar token aquí también
    # Por simplicidad, usamos un user_id simulado
    user_id = 1
    
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
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enviar mensaje de chat vía REST."""
    response = await process_message(
        request.message,
        request.case_id,
        request.module
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