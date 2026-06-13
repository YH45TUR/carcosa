"""
Sistema Legal CO - Documentos
Upload, descarga y procesamiento de documentos asociados a casos.
Fase 2: procesamiento asincrono via Celery, endpoint de lista por caso.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import json
import uuid
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.case import Case, CaseDocument
from app.config import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tiff"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ─ Helpers ─────────────────────────────────────────────────────────────────

def _doc_to_dict(doc: CaseDocument) -> dict:
    return {
        "id": doc.id,
        "case_id": doc.case_id,
        "filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "processing_status": "done" if doc.extracted_text else "pending",
        "has_text": bool(doc.extracted_text),
        "has_metadata": bool(doc.extracted_metadata),
        "created_at": doc.created_at.isoformat(),
    }


# ─ Endpoints ───────────────────────────────────────────────────────────────

@router.get("/by-case/{case_id}", response_model=List[dict])
def list_case_documents(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos los documentos de un caso."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    docs = db.query(CaseDocument).filter(CaseDocument.case_id == case_id).all()
    return [_doc_to_dict(d) for d in docs]


@router.post("/upload/{case_id}")
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sube un documento y lo asocia al caso.
    El procesamiento (OCR + NER + vectorizacion) se encola en Celery.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    if current_user.role == UserRole.asistente and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso a este caso")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo no soportado: {ext}. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 50 MB)")

    # Guardar en disco
    upload_dir = settings.uploads_dir
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Crear registro
    document = CaseDocument(
        case_id=case_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=len(content),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Encolar procesamiento async en Celery
    # Si Celery no está disponible, procesar inline como fallback
    job_id = None
    try:
        from app.core.tasks import process_document_task
        task = process_document_task.delay(document.id)
        job_id = task.id
    except Exception:
        # Fallback: procesamiento síncrono (sin Redis)
        try:
            from app.modules.extraction.batch_processor import BatchProcessor
            processor = BatchProcessor()
            result = await processor.process_file(file_path, enable_ner=True)
            if result.get("text"):
                document.extracted_text = result["text"][:50000]
            if result.get("entities"):
                document.extracted_metadata = json.dumps(result["entities"], ensure_ascii=False, default=str)
            db.commit()
        except Exception:
            pass  # El documento se guarda aunque falle el procesamiento

    return {
        **_doc_to_dict(document),
        "job_id": job_id,
        "message": (
            "Documento subido. Procesamiento en cola." if job_id
            else "Documento subido y procesado."
        ),
    }


@router.post("/upload-multiple/{case_id}")
async def upload_multiple(
    case_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sube múltiples documentos y los encola para procesamiento."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    if current_user.role == UserRole.asistente and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    uploaded, errors = [], []
    for f in files:
        try:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                errors.append({"filename": f.filename, "error": f"Tipo no soportado: {ext}"})
                continue
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append({"filename": f.filename, "error": "Demasiado grande"})
                continue

            upload_dir = settings.uploads_dir
            os.makedirs(upload_dir, exist_ok=True)
            unique_name = f"{uuid.uuid4().hex}{ext}"
            path = os.path.join(upload_dir, unique_name)
            with open(path, "wb") as fp:
                fp.write(content)

            doc = CaseDocument(
                case_id=case_id, filename=unique_name,
                original_filename=f.filename, file_path=path,
                file_type=ext.lstrip("."), file_size=len(content),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            job_id = None
            try:
                from app.core.tasks import process_document_task
                job_id = process_document_task.delay(doc.id).id
            except Exception:
                pass

            uploaded.append({**_doc_to_dict(doc), "job_id": job_id})
        except Exception as e:
            errors.append({"filename": f.filename, "error": str(e)})

    return {"uploaded": len(uploaded), "errors": len(errors), "documents": uploaded, "error_details": errors}


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene metadatos e info de procesamiento de un documento."""
    doc = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return _doc_to_dict(doc)


@router.get("/{document_id}/text")
def get_document_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el texto y entidades extraidas de un documento."""
    doc = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {
        "id": doc.id,
        "filename": doc.original_filename,
        "extracted_text": doc.extracted_text or "",
        "entities": json.loads(doc.extracted_metadata) if doc.extracted_metadata else None,
    }


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Descarga el archivo original."""
    doc = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path=doc.file_path, filename=doc.original_filename)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.abogado])),
):
    """Elimina documento (admin/abogado)."""
    doc = db.query(CaseDocument).filter(CaseDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return None
