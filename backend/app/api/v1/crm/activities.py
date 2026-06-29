from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db, Empresa
from app.dashboard_api import obter_empresa

from app.schemas.crm import CrmActivityCreate, CrmActivityResponse
from app.services.crm import activity_service

router = APIRouter()

@router.post("/", response_model=CrmActivityResponse)
def create_activity(
    activity_in: CrmActivityCreate, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    return activity_service.create_activity(db, empresa.id, activity_in)

@router.get("/", response_model=List[CrmActivityResponse])
def list_activities(
    deal_id: Optional[UUID] = Query(None, description="Filtrar atividades por Negócio"),
    contact_id: Optional[UUID] = Query(None, description="Filtrar atividades por Contato"),
    skip: int = 0, 
    limit: int = 100, 
    empresa: Empresa = Depends(obter_empresa), 
    db: Session = Depends(get_db)
):
    if deal_id:
        return activity_service.get_activities_by_deal(db, deal_id, skip, limit)
    elif contact_id:
        return activity_service.get_activities_by_contact(db, contact_id, skip, limit)
    else:
        # Se nenhum filtro for passado, podemos retornar uma lista vazia ou erro
        # já que listar todas as atividades de todos os contatos pode ser muito pesado.
        return []
