from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException

from app.models.crm import CrmDeal, CrmPipeline
from app.schemas.crm import CrmDealCreate

def create_deal(db: Session, empresa_id: UUID, deal_in: CrmDealCreate) -> CrmDeal:
    # Validate Pipeline
    pipeline = db.query(CrmPipeline).filter(CrmPipeline.id == deal_in.pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    db_deal = CrmDeal(
        empresa_id=empresa_id,
        **deal_in.model_dump()
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def get_deal(db: Session, deal_id: UUID) -> Optional[CrmDeal]:
    return db.query(CrmDeal).filter(CrmDeal.id == deal_id).first()

def get_deals_by_empresa(db: Session, empresa_id: UUID, skip: int = 0, limit: int = 100) -> List[CrmDeal]:
    return db.query(CrmDeal).filter(CrmDeal.empresa_id == empresa_id).offset(skip).limit(limit).all()

def move_deal_stage(db: Session, deal_id: UUID, new_stage_id: str) -> Optional[CrmDeal]:
    deal = get_deal(db, deal_id)
    if not deal:
        return None
        
    deal.stage_id = new_stage_id
    db.commit()
    db.refresh(deal)
    return deal
