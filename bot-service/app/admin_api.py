from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db, Empresa, init_db
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid

router = APIRouter()

# Segurança básica via Token de Admin no Header
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "atendia-master-2026")

def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Não autorizado: Token de Admin inválido")

class EmpresaCreate(BaseModel):
    nome: str
    slug: str
    telefone_whatsapp: str
    telefone_proprietario: Optional[str] = None
    valor_mensalidade: Optional[float] = 0.0
    dias_teste: Optional[int] = 30
    cupom_vendedor: Optional[str] = None

class EmpresaResponse(BaseModel):
    id: uuid.UUID
    nome: str
    slug: str
    ativo: bool
    valor_mensalidade: float
    data_expiracao_teste: Optional[datetime]
    data_criacao: datetime

    class Config:
        from_attributes = True

@router.get("/empresas", response_model=List[EmpresaResponse], dependencies=[Depends(verify_admin)])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Empresa).all()

@router.post("/empresas", response_model=EmpresaResponse, dependencies=[Depends(verify_admin)])
def criar_empresa(data: EmpresaCreate, db: Session = Depends(get_db)):
    # Verifica se slug já existe
    existente = db.query(Empresa).filter(Empresa.slug == data.slug).first()
    if existente:
        raise HTTPException(status_code=400, detail="Este slug já está em uso")
    
    # Calcula data de expiração
    expiracao = None
    if data.dias_teste > 0:
        from datetime import timedelta
        expiracao = datetime.now() + timedelta(days=data.dias_teste)

    nova_empresa = Empresa(
        nome=data.nome,
        slug=data.slug,
        telefone_whatsapp=data.telefone_whatsapp,
        telefone_proprietario=data.telefone_proprietario,
        valor_mensalidade=data.valor_mensalidade,
        data_expiracao_teste=expiracao,
        cupom_vendedor=data.cupom_vendedor
    )
    
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    return nova_empresa

@router.patch("/empresas/{empresa_id}/status", dependencies=[Depends(verify_admin)])
def alternar_status_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.ativo = not empresa.ativo
    db.commit()
    return {"status": "ok", "novo_status": empresa.ativo}
