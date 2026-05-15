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
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_TOKEN não configurado no ambiente. Abortando.")

import logging
logger = logging.getLogger(__name__)

def verify_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        logger.warning("Tentativa de acesso admin com token inválido.")
        raise HTTPException(status_code=401, detail="Não autorizado")

class TemplateCreate(BaseModel):
    nome_nicho: str
    prompt_sistema: str
    tom_voz: Optional[str] = None
    missao: Optional[str] = None
    objetivo: Optional[str] = None
    etapas_funil: Optional[List[str]] = None
    nicho: Optional[str] = "generico"

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
    etapas_funil: Optional[List[str]] = None
    plano: Optional[str] = "trial"
    limite_conversas_mes: Optional[int] = 100
    nicho: Optional[str] = "generico"

class EmpresaResponse(BaseModel):
    id: uuid.UUID
    nome: str
    slug: Optional[str] = None
    ativo: bool
    valor_mensalidade: float
    data_expiracao_teste: Optional[datetime] = None
    data_criacao: Optional[datetime] = None
    
    plano: str
    limite_conversas_mes: int
    conversas_mes_atual: int
    tokens_input_mes: int
    tokens_output_mes: int
    custo_estimado_usd: Optional[float] = 0.0

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

@router.put("/templates/{template_id}", dependencies=[Depends(verify_admin)])
def atualizar_template(template_id: uuid.UUID, data: TemplateCreate, db: Session = Depends(get_db)):
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    for key, value in data.dict().items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}", dependencies=[Depends(verify_admin)])
def excluir_template(template_id: uuid.UUID, db: Session = Depends(get_db)):
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    db.delete(template)
    db.commit()
    return {"status": "ok", "message": "Template excluído com sucesso"}

@router.get("/empresas", response_model=List[EmpresaResponse], dependencies=[Depends(verify_admin)])
def listar_empresas(db: Session = Depends(get_db)):
    empresas = db.query(Empresa).all()
    import re
    for emp in empresas:
        if not emp.slug:
            emp.slug = re.sub(r'[^a-z0-9]+', '-', emp.nome.lower()).strip('-')
        # Calcula custo estimado USD (gpt-4o-mini pricing)
        emp.custo_estimado_usd = ((emp.tokens_input_mes or 0) * 0.00000015) + ((emp.tokens_output_mes or 0) * 0.0000006)
    db.commit()
    return empresas

@router.get("/financeiro/resumo", dependencies=[Depends(verify_admin)])
def resumo_financeiro(db: Session = Depends(get_db)):
    empresas = db.query(Empresa).filter(Empresa.ativo == True).all()
    
    total_clientes = len(empresas)
    mrr = sum(emp.valor_mensalidade or 0 for emp in empresas)
    
    total_tokens_in = sum(emp.tokens_input_mes or 0 for emp in empresas)
    total_tokens_out = sum(emp.tokens_output_mes or 0 for emp in empresas)
    
    # Custo estimado total em USD
    custo_ia_usd = (total_tokens_in * 0.00000015) + (total_tokens_out * 0.0000006)
    
    # Detalhamento por plano
    planos_count = {
        "trial": db.query(Empresa).filter(Empresa.plano == "trial", Empresa.ativo == True).count(),
        "starter": db.query(Empresa).filter(Empresa.plano == "starter", Empresa.ativo == True).count(),
        "pro": db.query(Empresa).filter(Empresa.plano == "pro", Empresa.ativo == True).count(),
        "ilimitado": db.query(Empresa).filter(Empresa.plano == "ilimitado", Empresa.ativo == True).count(),
    }
    
    return {
        "total_clientes": total_clientes,
        "mrr": mrr,
        "custo_ia_usd": custo_ia_usd,
        "planos": planos_count
    }

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
        cupom_vendedor=data.cupom_vendedor,
        plano=data.plano,
        limite_conversas_mes=data.limite_conversas_mes,
        nicho=data.nicho
    )

    # Se forneceu etapas diretamente
    if data.etapas_funil:
        nova_empresa.etapas_funil = data.etapas_funil
    
    # Se escolheu um template, herda as etapas dele (se o template tiver)
    if data.template_id:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == data.template_id).first()
        if template and template.etapas_funil:
            nova_empresa.etapas_funil = template.etapas_funil
        if template and template.nicho:
            nova_empresa.nicho = template.nicho
    
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

@router.put("/empresas/{empresa_id}", dependencies=[Depends(verify_admin)])
def atualizar_empresa(empresa_id: uuid.UUID, data: EmpresaCreate, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Atualiza campos básicos
    empresa.nome = data.nome
    empresa.slug = data.slug
    empresa.valor_mensalidade = data.valor_mensalidade
    empresa.plano = data.plano
    empresa.limite_conversas_mes = data.limite_conversas_mes
    empresa.nicho = data.nicho
    
    # Se mudar o template, atualiza a configuração (opcional/decisão de design)
    if data.template_id:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == data.template_id).first()
        if template:
            empresa.etapas_funil = template.etapas_funil
            empresa.nicho = template.nicho
            
            # Atualiza o prompt na tabela de configuracoes
            config = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
            if config:
                new_config = config.config.copy()
                new_config.update({
                    "prompt_sistema": template.prompt_sistema,
                    "tom_voz": template.tom_voz,
                    "missao": template.missao,
                    "objetivo": template.objetivo
                })
                config.config = new_config

    db.commit()
    return {"status": "ok", "message": "Empresa atualizada com sucesso"}

@router.post("/empresas/{empresa_id}/impersonate", dependencies=[Depends(verify_admin)])
def impersonate_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Busca o primeiro usuário da empresa para gerar o token
    usuario = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Esta empresa não possui usuários cadastrados")
    
    import re
    slug = empresa.slug
    if not slug:
        # Gera um slug temporário/permanente baseado no nome
        slug = re.sub(r'[^a-z0-9]+', '-', empresa.nome.lower()).strip('-')
        empresa.slug = slug
        db.commit()

    from app.auth import create_access_token
    access_token = create_access_token(data={"sub": str(empresa.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "slug": slug
    }

@router.get("/debug/trigger-reports", dependencies=[Depends(verify_admin)])
def trigger_reports_manual():
    """Gatilho manual para testar o envio de relatórios semanais."""
    try:
        from app.main import tarefa_relatorio_semanal
        tarefa_relatorio_semanal()
        return {"status": "ok", "message": "Disparo de relatórios iniciado com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao disparar relatórios manuais: {e}")
        raise HTTPException(status_code=500, detail=str(e))
