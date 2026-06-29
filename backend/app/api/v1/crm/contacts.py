from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db, Empresa
from app.dashboard_api import obter_empresa

from app.schemas.crm import CrmContactCreate, CrmContactResponse
from app.services.crm import contact_service

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
