from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db, Empresa, PromptTemplate, Configuracao, Usuario, init_db
from app.auth import get_password_hash
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid

router = APIRouter()

# Segurança básica via Token de Admin no Header
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "atendia-master-2026")

import logging
logger = logging.getLogger(__name__)

def verify_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    # Log para depuração (Removeremos depois)
    logger.info(f"Tentativa de login ADM com token: {x_admin_token}")
    
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        logger.warning(f"Acesso Negado! Esperado: {ADMIN_TOKEN} | Recebido: {x_admin_token}")
        raise HTTPException(status_code=401, detail="Não autorizado: Token de Admin inválido")

class TemplateCreate(BaseModel):
    nome_nicho: str
    prompt_sistema: str
    tom_voz: Optional[str] = None
    missao: Optional[str] = None
    objetivo: Optional[str] = None

class EmpresaCreate(BaseModel):
    nome: str
    slug: str
    telefone_whatsapp: str
    email_admin: str
    senha_admin: str
    telefone_proprietario: Optional[str] = None
    valor_mensalidade: Optional[float] = 0.0
    dias_teste: Optional[int] = 30
    cupom_vendedor: Optional[str] = None
    template_id: Optional[uuid.UUID] = None

class EmpresaResponse(BaseModel):
    id: uuid.UUID
    nome: str
    slug: Optional[str] = None
    ativo: bool
    valor_mensalidade: float
    data_expiracao_teste: Optional[datetime]
    data_criacao: datetime

    class Config:
        from_attributes = True

@router.get("/templates", dependencies=[Depends(verify_admin)])
def listar_templates(db: Session = Depends(get_db)):
    return db.query(PromptTemplate).all()

@router.post("/templates", dependencies=[Depends(verify_admin)])
def criar_template(data: TemplateCreate, db: Session = Depends(get_db)):
    novo = PromptTemplate(**data.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

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

    # Aplica o Template se fornecido
    config_data = {}
    if data.template_id:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == data.template_id).first()
        if template:
            config_data = {
                "prompt_sistema": template.prompt_sistema,
                "tom_voz": template.tom_voz,
                "missao": template.missao,
                "objetivo": template.objetivo
            }
    
    # Cria a configuração inicial
    nova_config = Configuracao(
        empresa_id=nova_empresa.id,
        config=config_data
    )
    db.add(nova_config)
    db.commit()

    # Cria o usuário admin da empresa
    novo_usuario = Usuario(
        email=data.email_admin,
        senha_hash=get_password_hash(data.senha_admin),
        empresa_id=nova_empresa.id
    )
    db.add(novo_usuario)
    db.commit()

    return nova_empresa

@router.patch("/empresas/{empresa_id}/status", dependencies=[Depends(verify_admin)])
def alternar_status_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.ativo = not empresa.ativo
    db.commit()
    return {"status": "ok", "novo_status": empresa.ativo}

@router.delete("/empresas/{empresa_id}", dependencies=[Depends(verify_admin)])
def excluir_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    db.delete(empresa)
    db.commit()
    return {"status": "ok", "message": "Empresa excluída com sucesso"}

@router.post("/empresas/{empresa_id}/impersonate", dependencies=[Depends(verify_admin)])
def impersonate_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Busca o primeiro usuário da empresa para gerar o token
    usuario = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Esta empresa não possui usuários cadastrados")
    
    from app.auth import create_access_token
    access_token = create_access_token(data={"sub": usuario.email, "empresa_id": str(empresa.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "slug": empresa.slug
    }
