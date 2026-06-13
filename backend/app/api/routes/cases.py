"""
Sistema Legal CO - Gestión de Casos
CRUD completo de casos con permisos por rol.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus, LegalArea

router = APIRouter()


# === SCHEMAS ===

class CaseCreate(BaseModel):
    cliente: str
    demandado: Optional[str] = None
    area: LegalArea
    radicado: Optional[str] = None
    juzgado: Optional[str] = None
    cuantia: Optional[float] = None
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    cliente: Optional[str] = None
    demandado: Optional[str] = None
    area: Optional[LegalArea] = None
    status: Optional[CaseStatus] = None
    radicado: Optional[str] = None
    juzgado: Optional[str] = None
    cuantia: Optional[float] = None
    description: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    radicado: Optional[str]
    cliente: str
    demandado: Optional[str]
    area: LegalArea
    status: CaseStatus
    juzgado: Optional[str]
    cuantia: Optional[float]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# === ENDPOINTS ===

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear nuevo caso."""
    # Verificar si el radicado ya existe
    if case_data.radicado:
        existing = db.query(Case).filter(Case.radicado == case_data.radicado).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un caso con este radicado"
            )
    
    case = Case(
        **case_data.model_dump(),
        owner_id=current_user.id
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[CaseStatus] = None,
    area: Optional[LegalArea] = None,
    cliente: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar casos con filtros."""
    query = db.query(Case)
    
    # Filtrar por status
    if status:
        query = query.filter(Case.status == status)
    
    # Filtrar por área
    if area:
        query = query.filter(Case.area == area)
    
    # Filtrar por cliente (búsqueda parcial)
    if cliente:
        query = query.filter(Case.cliente.ilike(f"%{cliente}%"))
    
    # Admin y abogado ven todos, asistente ve solo los propios
    if current_user.role == UserRole.asistente:
        query = query.filter(Case.owner_id == current_user.id)
    
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener caso por ID."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Verificar acceso
    if current_user.role == UserRole.asistente and case.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este caso")
    
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin, UserRole.abogado]))
):
    """Actualizar caso."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Actualizar campos
    for field, value in case_data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Eliminar caso (solo admin)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    db.delete(case)
    db.commit()
    return None