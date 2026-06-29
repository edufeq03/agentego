from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db, Empresa
from app.dashboard_api import obter_empresa

from app.schemas.crm import CrmContactCreate, CrmContactResponse, CrmContextResponse
from app.services.crm import contact_service, context_extractor
from app.models.crm import CrmContext

router = APIRouter()

@router.post("/", response_model=CrmContactResponse)
def create_contact(
    contact_in: CrmContactCreate, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return contact_service.create_contact(db, empresa.id, contact_in)

@router.get("/", response_model=List[CrmContactResponse])
def list_contacts(
    skip: int = 0, 
    limit: int = 100, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return contact_service.get_contacts_by_empresa(db, empresa.id, skip, limit)

@router.post("/import-lead/{lead_id}", response_model=CrmContactResponse)
def import_lead_to_contact(
    lead_id: UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    contact = contact_service.convert_lead_to_contact(db, lead_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Lead not found or does not belong to this company")
    return contact

@router.get("/{contact_id}/context", response_model=CrmContextResponse)
def get_contact_context(
    contact_id: UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    context = db.query(CrmContext).filter(CrmContext.contact_id == contact_id, CrmContext.empresa_id == empresa.id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Contexto não encontrado para este contato")
    return context

@router.post("/{contact_id}/summarize", response_model=CrmContextResponse)
def summarize_contact(
    contact_id: UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    return context_extractor.generate_ai_summary(db, empresa.id, contact_id)
