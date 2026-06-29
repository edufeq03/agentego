from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db, Empresa
from app.dashboard_api import obter_empresa

from app.schemas.crm import CrmPipelineCreate, CrmPipelineResponse
from app.services.crm import pipeline_service

router = APIRouter()

@router.post("/", response_model=CrmPipelineResponse)
def create_pipeline(
    pipeline_in: CrmPipelineCreate, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return pipeline_service.create_pipeline(db, empresa.id, pipeline_in)

@router.get("/", response_model=List[CrmPipelineResponse])
def list_pipelines(
    skip: int = 0, 
    limit: int = 100, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return pipeline_service.get_pipelines_by_empresa(db, empresa.id, skip, limit)
