from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.crm import CrmActivity
from app.schemas.crm import CrmActivityCreate

def create_activity(db: Session, empresa_id: UUID, activity_in: CrmActivityCreate) -> CrmActivity:
    db_activity = CrmActivity(
        empresa_id=empresa_id,
        **activity_in.model_dump()
    )
    if activity_in.done and not activity_in.done_at:
        db_activity.done_at = datetime.utcnow()
        
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def get_activity(db: Session, activity_id: UUID) -> Optional[CrmActivity]:
    return db.query(CrmActivity).filter(CrmActivity.id == activity_id).first()

def get_activities_by_deal(db: Session, deal_id: UUID, skip: int = 0, limit: int = 100) -> List[CrmActivity]:
    return db.query(CrmActivity).filter(CrmActivity.deal_id == deal_id).order_by(CrmActivity.created_at.desc()).offset(skip).limit(limit).all()

def get_activities_by_contact(db: Session, contact_id: UUID, skip: int = 0, limit: int = 100) -> List[CrmActivity]:
    return db.query(CrmActivity).filter(CrmActivity.contact_id == contact_id).order_by(CrmActivity.created_at.desc()).offset(skip).limit(limit).all()
