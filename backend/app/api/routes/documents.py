"""
Sistema Legal CO - Documentos
Upload, descarga y procesamiento de documentos asociados a casos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
import shutil
import uuid
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.case import Case, CaseDocument
from app.modules.extraction.batch_processor import BatchProcessor
from app.config import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload/{case_id}")
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sube un documento y lo asocia a un caso.
    Inicia el procesamiento asíncrono del documento.
    """
    # Validar caso
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    # Verificar acceso
    if current_user.role == UserRole.asistente and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este caso")

    # Validar archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {ext}. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validar tamaño
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    # Guardar archivo
    upload_dir = settings.uploads_dir
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Crear registro en DB
    document = CaseDocument(
        case_id=case_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=file_size,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Iniciar procesamiento asíncrono
    # Nota: En producción, esto iría a una cola de tareas (Celery/Redis)
    # Por ahora, procesamos en background
    try:
        processor = BatchProcessor()
        result = await processor.process_file(
            file_path=file_path,
            chunk_strategy="by_size",
            enable_ner=True,
            enable_vector_store=False,
        )

        # Guardar resultados del procesamiento
        if result.get("text"):
            document.extracted_text = result["text"][:50000]  # Limitar tamaño

        if result.get("entities"):
            document.extracted_metadata = json.dumps(result["entities"], ensure_ascii=False, default=str)

        if result.get("chunks"):
            document.chunks = json.dumps(result["chunks"], ensure_ascii=False)

        db.commit()
        processing_status = result.get("status", "completed")
    except Exception as e:
        processing_status = f"error: {str(e)}"

    return {
        "id": document.id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "processing_status": processing_status,
        "created_at": document.created_at.isoformat(),
    }


@router.post("/upload-multiple/{case_id}")
async def upload_multiple_documents(
    case_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sube múltiples documentos y los asocia a un caso.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if current_user.role == UserRole.asistente and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este caso")

    results = []
    errors = []

    for uploaded_file in files:
        try:
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                errors.append({"filename": uploaded_file.filename, "error": f"Tipo no soportado: {ext}"})
                continue

            upload_dir = settings.uploads_dir
            os.makedirs(upload_dir, exist_ok=True)

            content = await uploaded_file.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append({"filename": uploaded_file.filename, "error": "Archivo demasiado grande"})
                continue

            unique_filename = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, "wb") as f:
                f.write(content)

            document = CaseDocument(
                case_id=case_id,
                filename=unique_filename,
                original_filename=uploaded_file.filename,
                file_path=file_path,
                file_type=ext.lstrip("."),
                file_size=len(content),
            )
            db.add(document)
            db.commit()

            results.append({
                "id": document.id,
                "filename": document.original_filename,
                "status": "uploaded",
            })

        except Exception as e:
            errors.append({"filename": uploaded_file.filename, "error": str(e)})

    return {
        "uploaded": len(results),
        "errors": len(errors),
        "documents": results,
        "error_details": errors,
    }


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene información de un documento.
    """
    document = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Verificar acceso
    case = db.query(Case).filter(Case.id == document.case_id).first()
    if current_user.role == UserRole.asistente and case and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este documento")

    return {
        "id": document.id,
        "case_id": document.case_id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "has_extracted_text": bool(document.extracted_text),
        "has_metadata": bool(document.extracted_metadata),
        "created_at": document.created_at.isoformat(),
    }


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Descarga un documento.
    """
    document = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type="application/octet-stream",
    )


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene el texto extraído de un documento.
    """
    document = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return {
        "id": document.id,
        "filename": document.original_filename,
        "extracted_text": document.extracted_text or "",
        "extracted_metadata": json.loads(document.extracted_metadata) if document.extracted_metadata else None,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.abogado])),
):
    """
    Elimina un documento (solo admin/abogado).
    """
    document = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo físico
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return None
