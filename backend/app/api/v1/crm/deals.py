from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db, Empresa
from app.dashboard_api import obter_empresa

from app.schemas.crm import CrmDealCreate, CrmDealResponse, DealStageUpdate
from app.services.crm import deal_service

router = APIRouter()

@router.post("/", response_model=CrmDealResponse)
def create_deal(
    deal_in: CrmDealCreate, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return deal_service.create_deal(db, empresa.id, deal_in)

@router.post("/from-lead/{lead_id}", response_model=CrmDealResponse)
def create_deal_from_lead(
    lead_id: UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    return deal_service.convert_lead_to_deal(db, empresa.id, lead_id)

@router.get("/", response_model=List[CrmDealResponse])
def list_deals(
    skip: int = 0, 
    limit: int = 100, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return deal_service.get_deals_by_empresa(db, empresa.id, skip, limit)

@router.patch("/{deal_id}/stage", response_model=CrmDealResponse)
def update_deal_stage(
    deal_id: UUID,
    stage_update: DealStageUpdate,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    deal = deal_service.move_deal_stage(db, deal_id, stage_update.stage_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
