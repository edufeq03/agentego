import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db, Empresa, Servico, Disponibilidade, Bloqueio, Agendamento, Lead, Configuracao
from app.dashboard_api import obter_empresa
from app.agenda_service import (
    calcular_slots,
    criar_agendamento_cliente,
    confirmar_agendamento,
    recusar_agendamento,
    cancelar_agendamento,
    hm_to_min,
    min_to_hm
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to verify if the company has the agenda module active
def verificar_agenda_ativa(empresa: Empresa = Depends(obter_empresa)) -> Empresa:
    config_dict = empresa.configuracoes.config if empresa.configuracoes else {}
    modulos = config_dict.get("modulos_ativos", [])
    # Se não houver modulos_ativos configurados, aceita por padrão para facilitar testes/desenvolvimento
    if config_dict and "agenda" not in modulos:
        # Para evitar bloquear caso a empresa não tenha a chave configurada na migração:
        # Se modulos_ativos não existir ou estiver vazio, consideramos habilitado.
        if "modulos_ativos" in config_dict:
            raise HTTPException(status_code=400, detail="Módulo Agenda não está ativo para esta empresa.")
    return empresa

# Schemas
class ServicoSchema(BaseModel):
    nome: str
    descricao: Optional[str] = ""
    duracao_min: int
    preco: Optional[float] = None
    ativo: Optional[bool] = True
    cor: Optional[str] = "#3b82f6"
    ordem: Optional[int] = 0
    tem_variacao_caracteristica: Optional[bool] = False
    caracteristicas: Optional[dict] = None
    recorrencia_sugerida_dias: Optional[int] = None

class DisponibilidadeSchema(BaseModel):
    dia_semana: int
    hora_inicio: str
    hora_fim: str
    intervalo_min: Optional[int] = 30
    ativo: Optional[bool] = True

class BloqueioSchema(BaseModel):
    data: str
    hora_inicio: str
    hora_fim: str
    motivo: Optional[str] = ""

class StatusUpdateSchema(BaseModel):
    status: str
    motivo: Optional[str] = ""

class AgendamentoManualSchema(BaseModel):
    lead_id: Optional[str] = None
    cliente_nome: Optional[str] = ""
    cliente_telefone: Optional[str] = ""
    servico_id: str
    data: str
    hora_inicio: str
    observacao: Optional[str] = ""

class AgendaConfigSchema(BaseModel):
    aprovacao_manual: Optional[bool] = True
    whatsapp_profissional: Optional[str] = None
    lembrete_cliente_min: Optional[int] = 120
    lembrete_profissional_hora: Optional[str] = "08:00"
    resumo_semanal_dia: Optional[int] = 0
    resumo_semanal_hora: Optional[str] = "07:00"
    aprovacao_timeout_min: Optional[int] = 60

# --- SERVICOS ---
@router.get("/servicos")
def get_servicos(empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    return db.query(Servico).filter(Servico.empresa_id == empresa.id).order_by(Servico.ordem.asc(), Servico.nome.asc()).all()

@router.post("/servicos")
def create_servico(payload: ServicoSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    servico = Servico(
        empresa_id=empresa.id,
        nome=payload.nome,
        descricao=payload.descricao,
        duracao_min=payload.duracao_min,
        preco=payload.preco,
        ativo=payload.ativo,
        cor=payload.cor,
        ordem=payload.ordem,
        tem_variacao_caracteristica=payload.tem_variacao_caracteristica,
        caracteristicas=payload.caracteristicas,
        recorrencia_sugerida_dias=payload.recorrencia_sugerida_dias
    )
    db.add(servico)
    db.commit()
    db.refresh(servico)
    return servico

@router.put("/servicos/{id}")
def update_servico(id: str, payload: ServicoSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    servico = db.query(Servico).filter(Servico.id == id, Servico.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    servico.nome = payload.nome
    servico.descricao = payload.descricao
    servico.duracao_min = payload.duracao_min
    servico.preco = payload.preco
    servico.ativo = payload.ativo
    servico.cor = payload.cor
    servico.ordem = payload.ordem
    servico.tem_variacao_caracteristica = payload.tem_variacao_caracteristica
    servico.caracteristicas = payload.caracteristicas
    servico.recorrencia_sugerida_dias = payload.recorrencia_sugerida_dias
    
    db.commit()
    db.refresh(servico)
    return servico

@router.delete("/servicos/{id}")
def delete_servico(id: str, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    servico = db.query(Servico).filter(Servico.id == id, Servico.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    db.delete(servico)
    db.commit()
    return {"status": "ok", "mensagem": "Serviço excluído com sucesso"}

# --- DISPONIBILIDADE ---
@router.get("/disponibilidade")
def get_disponibilidade(empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    return db.query(Disponibilidade).filter(Disponibilidade.empresa_id == empresa.id).order_by(Disponibilidade.dia_semana.asc()).all()

@router.post("/disponibilidade")
def save_disponibilidade(payload: List[DisponibilidadeSchema], empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    try:
        # Delete existing standard availability
        db.query(Disponibilidade).filter(Disponibilidade.empresa_id == empresa.id).delete()
        for item in payload:
            new_disp = Disponibilidade(
                empresa_id=empresa.id,
                dia_semana=item.dia_semana,
                hora_inicio=item.hora_inicio,
                hora_fim=item.hora_fim,
                intervalo_min=item.intervalo_min,
                ativo=item.ativo
            )
            db.add(new_disp)
        db.commit()
        return {"status": "ok", "mensagem": "Disponibilidade salva com sucesso"}
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar disponibilidade: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar disponibilidade")

# --- BLOQUEIOS ---
@router.get("/bloqueios")
def get_bloqueios(empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    return db.query(Bloqueio).filter(Bloqueio.empresa_id == empresa.id).order_by(Bloqueio.data.asc(), Bloqueio.hora_inicio.asc()).all()

@router.post("/bloqueios")
def create_bloqueio(payload: BloqueioSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    bloqueio = Bloqueio(
        empresa_id=empresa.id,
        data=payload.data,
        hora_inicio=payload.hora_inicio,
        hora_fim=payload.hora_fim,
        motivo=payload.motivo
    )
    db.add(bloqueio)
    db.commit()
    db.refresh(bloqueio)
    return bloqueio

@router.delete("/bloqueios/{id}")
def delete_bloqueio(id: str, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    bloqueio = db.query(Bloqueio).filter(Bloqueio.id == id, Bloqueio.empresa_id == empresa.id).first()
    if not bloqueio:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado")
    db.delete(bloqueio)
    db.commit()
    return {"status": "ok", "mensagem": "Bloqueio excluído com sucesso"}

# --- AGENDAMENTOS ---
@router.get("/agendamentos")
def get_agendamentos(
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    empresa: Empresa = Depends(verificar_agenda_ativa),
    db: Session = Depends(get_db)
):
    query = db.query(Agendamento).filter(Agendamento.empresa_id == empresa.id)
    
    if status:
        query = query.filter(Agendamento.status == status)
    if data_inicio:
        query = query.filter(Agendamento.data >= data_inicio)
    if data_fim:
        query = query.filter(Agendamento.data <= data_fim)
        
    agendamentos = query.order_by(Agendamento.data.asc(), Agendamento.hora_inicio.asc()).all()
    
    # Adicionar o objeto Lead completo para o frontend renderizar o nome e telefone do cliente
    result = []
    for a in agendamentos:
        lead = db.query(Lead).filter(Lead.id == a.lead_id).first()
        result.append({
            "id": a.id,
            "data": a.data,
            "hora_inicio": a.hora_inicio,
            "hora_fim": a.hora_fim,
            "status": a.status,
            "observacao": a.observacao,
            "motivo_cancelamento": a.motivo_cancelamento,
            "servico_nome": a.servico_nome,
            "servico_duracao": a.servico_duracao,
            "caracteristica": a.caracteristica,
            "lead": {
                "id": lead.id if lead else None,
                "nome": lead.nome if lead else "Cliente Manual",
                "telefone": lead.telefone if lead else ""
            } if lead else None
        })
    return result

@router.post("/agendamentos")
def create_agendamento_manual(payload: AgendamentoManualSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    # Se não houver lead_id, criamos ou buscamos o lead pelo telefone
    lead_id = payload.lead_id
    if not lead_id:
        if not payload.cliente_nome or not payload.cliente_telefone:
            raise HTTPException(status_code=400, detail="Para novos agendamentos manuais, informe o nome e telefone do cliente.")
        
        # Normaliza telefone
        telefone = payload.cliente_telefone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not telefone.startswith("55"):
            telefone = "55" + telefone
            
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
        if not lead:
            lead = Lead(
                empresa_id=empresa.id,
                nome=payload.cliente_nome,
                telefone=telefone,
                stage="agendado"
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
        lead_id = lead.id

    # Busca o serviço
    servico = db.query(Servico).filter(Servico.id == payload.servico_id, Servico.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
        
    from app.agenda_service import criar_agendamento
    
    agendamento = criar_agendamento(
        db=db,
        empresa_id=empresa.id,
        lead_id=lead_id,
        servico_id=payload.servico_id,
        data_str=payload.data,
        hora_inicio=payload.hora_inicio,
        observacao=payload.observacao,
        status="confirmado"
    )
    
    if not agendamento:
        raise HTTPException(status_code=400, detail="Não foi possível criar o agendamento.")
        
    return agendamento

@router.patch("/agendamentos/{id}/status")
@router.put("/agendamentos/{id}/status")
def update_agendamento_status(id: int, payload: StatusUpdateSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    agendamento = db.query(Agendamento).filter(Agendamento.id == id, Agendamento.empresa_id == empresa.id).first()
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        
    sucesso = False
    if payload.status == "confirmado":
        sucesso = confirmar_agendamento(db, id)
    elif payload.status == "recusado":
        sucesso = recusar_agendamento(db, id, payload.motivo)
    elif payload.status == "cancelado":
        sucesso = cancelar_agendamento(db, id, payload.motivo)
        
    if not sucesso:
        raise HTTPException(status_code=400, detail="Não foi possível alterar o status do agendamento.")
        
    return {"status": "ok", "mensagem": f"Agendamento atualizado para {payload.status}"}

# --- SLOTS DE HORARIO ---
@router.get("/slots")
def get_slots(
    servico_id: str,
    data: str,
    empresa: Empresa = Depends(verificar_agenda_ativa),
    db: Session = Depends(get_db)
):
    slots = calcular_slots(db, empresa.id, servico_id, data)
    return {"data": data, "slots": slots}

# --- CONFIGURACOES DA AGENDA ---
@router.get("/config")
def get_agenda_config(empresa: Empresa = Depends(verificar_agenda_ativa)):
    config_dict = empresa.configuracoes.config if empresa.configuracoes else {}
    agenda_config = config_dict.get("agenda", {
        "aprovacao_manual": True,
        "whatsapp_profissional": empresa.telefone_proprietario,
        "lembrete_cliente_min": 120,
        "lembrete_profissional_hora": "08:00",
        "resumo_semanal_dia": 0,
        "resumo_semanal_hora": "07:00",
        "aprovacao_timeout_min": 60
    })
    return agenda_config

@router.put("/config")
def save_agenda_config(payload: AgendaConfigSchema, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    config_obj = empresa.configuracoes
    if not config_obj:
        config_obj = Configuracao(empresa_id=empresa.id, config={})
        db.add(config_obj)
        db.commit()
        db.refresh(config_obj)
        
    # Clona e atualiza a configuração
    config_data = dict(config_obj.config) if config_obj.config else {}
    config_data["agenda"] = {
        "aprovacao_manual": payload.aprovacao_manual,
        "whatsapp_profissional": payload.whatsapp_profissional,
        "lembrete_cliente_min": payload.lembrete_cliente_min,
        "lembrete_profissional_hora": payload.lembrete_profissional_hora,
        "resumo_semanal_dia": payload.resumo_semanal_dia,
        "resumo_semanal_hora": payload.resumo_semanal_hora,
        "aprovacao_timeout_min": payload.aprovacao_timeout_min
    }
    
    config_obj.config = config_data
    db.commit()
    return {"status": "ok", "mensagem": "Configurações da agenda salvas com sucesso"}

@router.get("/lista_espera")
def get_lista_espera(empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    from app.database import ListaEspera
    items = db.query(ListaEspera).filter(ListaEspera.empresa_id == empresa.id).order_by(ListaEspera.data.desc(), ListaEspera.posicao.asc()).all()
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "data": item.data,
            "status": item.status,
            "posicao": item.posicao,
            "notificado_em": item.notificado_em.isoformat() if item.notificado_em else None,
            "cliente_nome": item.lead.nome if item.lead else "Cliente",
            "cliente_telefone": item.lead.telefone if item.lead else "",
            "servico_nome": item.servico.nome if item.servico else "Serviço"
        })
    return result

@router.delete("/lista_espera/{id}")
def delete_lista_espera(id: int, empresa: Empresa = Depends(verificar_agenda_ativa), db: Session = Depends(get_db)):
    from app.database import ListaEspera
    item = db.query(ListaEspera).filter(ListaEspera.id == id, ListaEspera.empresa_id == empresa.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item da lista de espera não encontrado")
    db.delete(item)
    db.commit()
    return {"status": "ok", "mensagem": "Removido da lista de espera com sucesso"}
