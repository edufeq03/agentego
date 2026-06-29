from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.crm import CrmPipeline
from app.schemas.crm import CrmPipelineCreate

def create_pipeline(db: Session, empresa_id: UUID, pipeline_in: CrmPipelineCreate) -> CrmPipeline:
    db_pipeline = CrmPipeline(
        empresa_id=empresa_id,
        **pipeline_in.model_dump()
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline

def get_pipeline(db: Session, pipeline_id: UUID) -> Optional[CrmPipeline]:
    return db.query(CrmPipeline).filter(CrmPipeline.id == pipeline_id).first()

def get_pipelines_by_empresa(db: Session, empresa_id: UUID, skip: int = 0, limit: int = 100) -> List[CrmPipeline]:
    return db.query(CrmPipeline).filter(CrmPipeline.empresa_id == empresa_id).offset(skip).limit(limit).all()
