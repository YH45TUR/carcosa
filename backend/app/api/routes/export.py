"""
Sistema Legal CO - Exportación
Endpoints para generar y exportar documentos legales a DOCX y PDF.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
import uuid
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.case import Case, CaseVersion
from app.modules.drafting.generator import DraftingGenerator
from app.modules.drafting.exporter_docx import DOCXExporter
from app.modules.drafting.exporter_pdf import PDFExporter
from app.config import settings

router = APIRouter()

EXPORT_DIR = os.path.join(settings.uploads_dir, "exports")


@router.post("/generate")
async def generate_document(
    message: str = Body(...),
    case_id: Optional[int] = Body(None),
    document_type: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Genera un documento legal a partir de una descripción textual.

    El documento se genera con LLM + plantilla Jinja2.
    Opcionalmente se guarda como versión en el caso.
    """
    case_data = None
    if case_id:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Caso no encontrado")

        # Extraer datos del caso para precargar template
        case_data = {
            "demandante": case.cliente,
            "demandado": case.demandado,
            "juzgado": case.juzgado,
            "radicado": case.radicado,
            "cuantia": f"${case.cuantia:,.2f}" if case.cuantia else None,
        }

    generator = DraftingGenerator()
    result = await generator.generate(
        message=message,
        case_id=case_id,
        document_type=document_type,
        case_data=case_data,
    )

    if not result["success"]:
        return result

    # Guardar versión en el caso si hay case_id
    if case_id and result.get("data", {}).get("content"):
        version = CaseVersion(
            case_id=case_id,
            document_type=result["data"]["document_type"],
            content=result["data"]["content"][:50000],
            created_by_id=current_user.id,
        )
        db.add(version)
        db.commit()

    return result


@router.post("/export/docx")
async def export_docx(
    content: str = Body(...),
    filename: str = Body("documento_legal"),
    case_id: Optional[int] = Body(None),
    document_type: str = Body("documento"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exporta contenido a archivo .docx con formato NTC 1486.
    """
    exporter = DOCXExporter()
    os.makedirs(EXPORT_DIR, exist_ok=True)

    output_filename = f"{filename}_{uuid.uuid4().hex[:8]}.docx"
    output_path = os.path.join(EXPORT_DIR, output_filename)

    try:
        await exporter.export_with_template(
            content=content,
            output_path=output_path,
            document_type=document_type,
            metadata={
                "title": filename,
                "author": current_user.username,
                "comments": f"Generado por {current_user.username} el {datetime.now().isoformat()}",
            },
        )

        # Guardar versión si asociado a caso
        if case_id:
            version = CaseVersion(
                case_id=case_id,
                document_type=document_type,
                content=content[:50000],
                file_path=output_path,
                created_by_id=current_user.id,
            )
            db.add(version)
            db.commit()

        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar DOCX: {str(e)}")


@router.post("/export/pdf")
async def export_pdf(
    content: str = Body(...),
    filename: str = Body("documento_legal"),
    case_id: Optional[int] = Body(None),
    document_type: str = Body("documento"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exporta contenido a archivo PDF con formato legal colombiano.
    """
    exporter = PDFExporter()
    os.makedirs(EXPORT_DIR, exist_ok=True)

    output_filename = f"{filename}_{uuid.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(EXPORT_DIR, output_filename)

    try:
        await exporter.export(
            content=content,
            output_path=output_path,
            metadata={
                "title": filename,
                "author": current_user.username,
                "subject": document_type,
            },
        )

        if case_id:
            version = CaseVersion(
                case_id=case_id,
                document_type=document_type,
                content=content[:50000],
                file_path=output_path,
                created_by_id=current_user.id,
            )
            db.add(version)
            db.commit()

        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/pdf",
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


@router.get("/versions/{case_id}")
async def get_case_versions(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene el historial de versiones de documentos de un caso.
    """
    versions = (
        db.query(CaseVersion)
        .filter(CaseVersion.case_id == case_id)
        .order_by(CaseVersion.created_at.desc())
        .all()
    )

    return [
        {
            "id": v.id,
            "document_type": v.document_type,
            "version_number": v.version_number,
            "has_file": bool(v.file_path),
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.get("/versions/{version_id}/download")
async def download_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Descarga un archivo de versión específico.
    """
    version = db.query(CaseVersion).filter(CaseVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versión no encontrada")

    if not version.file_path or not os.path.exists(version.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=version.file_path,
        filename=f"{version.document_type}_v{version.version_number}{os.path.splitext(version.file_path)[1]}",
    )
