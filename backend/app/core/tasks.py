"""
Celery — cola de tareas para operaciones pesadas.
Sin esto, un batch de 500 folios bloquea el servidor principal.

Tareas:
  - process_document: OCR + NER + vectorizacion de un documento
  - cleanup_expired_tokens_task: limpia blocklist de JWT cada hora
  - index_jurisprudencia: indexa sentencias en ChromaDB
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "sistema_legal",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
)

# Tareas periodicas
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.core.tasks.cleanup_expired_tokens_task",
        "schedule": 3600.0,
    },
}


@celery_app.task(bind=True, name="app.core.tasks.process_document", max_retries=3)
def process_document_task(self, document_id: int) -> dict:
    """
    Pipeline completo para un documento:
    1. Descarga del storage
    2. Extraccion de texto (PDF/DOCX/imagen + OCR si necesario)
    3. NER legal (radicado, juzgado, partes, fechas, normas)
    4. Vectorizacion en ChromaDB
    5. Actualiza processing_status en DB

    El frontend hace polling a GET /api/cases/{id}/documents/{doc_id}/status
    para mostrar progreso al usuario.
    """
    import asyncio
    try:
        from app.modules.extraction.batch_processor import process_single_document
        return asyncio.run(process_single_document(document_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.core.tasks.cleanup_expired_tokens_task")
def cleanup_expired_tokens_task() -> dict:
    """Limpia tokens JWT revocados expirados de la blocklist."""
    import asyncio
    from app.db.database import AsyncSessionLocal
    from app.core.security import cleanup_expired_tokens

    async def _run():
        async with AsyncSessionLocal() as db:
            count = await cleanup_expired_tokens(db)
        return {"deleted": count}

    return asyncio.run(_run())


@celery_app.task(bind=True, name="app.core.tasks.index_jurisprudencia", max_retries=2)
def index_jurisprudencia_task(self, sentencia_id: str, text: str, metadata: dict) -> dict:
    """Indexa una sentencia en ChromaDB (coleccion jurisprudencia)."""
    try:
        from app.db.vector_store import get_jurisprudencia_collection, ChunkStrategy
        col = get_jurisprudencia_collection()
        chunks = col.add_document(sentencia_id, text, metadata, ChunkStrategy.BY_SECTION)
        return {"sentencia_id": sentencia_id, "chunks_indexed": chunks}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
