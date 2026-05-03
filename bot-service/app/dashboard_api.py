from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any

from app.database import get_db, Empresa, Lead, Mensagem, Evento, Configuracao

router = APIRouter()

# Autenticação simples baseada no webhook_token para o MVP
def obter_empresa(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido")
    
    token = authorization.split(" ")[1]
    empresa = db.query(Empresa).filter(Empresa.webhook_token == token, Empresa.ativo == True).first()
    
    if not empresa:
        raise HTTPException(status_code=401, detail="Token inválido ou empresa inativa")
    
    return empresa

@router.get("/visao-geral")
def visao_geral(periodos_dias: int = 7, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    limite_data = datetime.utcnow() - timedelta(days=periodos_dias)
    
    # Total de conversas ativas (leads)
    total_leads = db.query(Lead).filter(Lead.empresa_id == empresa.id).count()
    
    # Leads criados no período
    leads_recentes = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.criado_em >= limite_data).count()
    
    # Leads interessados
    leads_interessados = db.query(Lead).filter(
        Lead.empresa_id == empresa.id, 
        Lead.stage.in_(["interessado", "quente", "agendado"])
    ).count()
    
    # Visitas aceitas (eventos)
    visitas = db.query(Evento).filter(
        Evento.empresa_id == empresa.id,
        Evento.tipo == "visita_aceita",
        Evento.timestamp >= limite_data
    ).count()
    
    # Mensagens por dia (Gráfico)
    mensagens_query = db.query(
        func.date(Mensagem.timestamp).label('dia'),
        func.count(Mensagem.id).label('quantidade')
    ).filter(
        Mensagem.empresa_id == empresa.id,
        Mensagem.tipo == "usuario",
        Mensagem.timestamp >= limite_data
    ).group_by(func.date(Mensagem.timestamp)).all()
    
    grafico_conversas = [{"dia": str(row.dia), "mensagens": row.quantidade} for row in mensagens_query]
    
    return {
        "cards": {
            "total_leads": total_leads,
            "leads_recentes": leads_recentes,
            "leads_interessados": leads_interessados,
            "visitas": visitas
        },
        "grafico_conversas": grafico_conversas
    }

@router.get("/funil")
def funil(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Contagem de leads por stage
    counts = db.query(Lead.stage, func.count(Lead.id)).filter(Lead.empresa_id == empresa.id).group_by(Lead.stage).all()
    
    # Inicializa com 0
    funil_data = {
        "novo": 0,
        "curioso": 0,
        "interessado": 0,
        "agendado": 0
    }
    
    for stage, count in counts:
        if stage in funil_data:
            funil_data[stage] = count
            
    # Formata para o Recharts
    grafico_funil = [
        {"name": "Total Contatos", "value": sum(funil_data.values()), "fill": "#8884d8"},
        {"name": "Curiosos", "value": funil_data["curioso"] + funil_data["interessado"] + funil_data["agendado"], "fill": "#83a6ed"},
        {"name": "Interessados", "value": funil_data["interessado"] + funil_data["agendado"], "fill": "#8dd1e1"},
        {"name": "Visitas Agendadas", "value": funil_data["agendado"], "fill": "#82ca9d"}
    ]
    
    return grafico_funil

@router.get("/intencoes")
def intencoes(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Contagem das intenções das mensagens
    counts = db.query(Mensagem.intencao, func.count(Mensagem.id)).filter(
        Mensagem.empresa_id == empresa.id,
        Mensagem.tipo == "usuario",
        Mensagem.intencao.isnot(None),
        Mensagem.intencao != "duvida" # Ignora a intenção genérica
    ).group_by(Mensagem.intencao).order_by(func.count(Mensagem.id).desc()).limit(5).all()
    
    grafico_intencoes = [{"name": intencao.capitalize(), "value": count} for intencao, count in counts]
    
    return grafico_intencoes

@router.get("/conversas")
def conversas(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Retorna as conversas recentes (Leads com mensagens)
    leads = db.query(Lead).filter(Lead.empresa_id == empresa.id).order_by(Lead.atualizado_em.desc()).all()
    
    resultado = []
    for lead in leads:
        # Última mensagem
        ultima_msg = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).first()
        if ultima_msg:
            # Check transbordo
            from app.pipeline import obter_status_transbordo
            status_transbordo = obter_status_transbordo(db, empresa.id, lead.telefone)
            
            resultado.append({
                "id": str(lead.id),
                "telefone": lead.telefone,
                "nome": lead.nome or lead.telefone,
                "stage": lead.stage,
                "ultima_mensagem": ultima_msg.mensagem,
                "timestamp": str(ultima_msg.timestamp),
                "transbordo": status_transbordo
            })
            
    return resultado

@router.get("/conversas/{telefone}")
def historico_conversa(telefone: str, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
        
    mensagens = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.asc()).all()
    
    return [{"tipo": m.tipo, "mensagem": m.mensagem, "timestamp": str(m.timestamp)} for m in mensagens]

@router.post("/conversas/{telefone}/pausar")
def pausar_robo(telefone: str, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.pipeline import atualizar_status_transbordo
    atualizar_status_transbordo(db, empresa.id, telefone, "pausado")
    return {"status": "ok", "mensagem": f"Robô pausado para {telefone}"}

@router.post("/conversas/{telefone}/reativar")
def reativar_robo_dashboard(telefone: str, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.pipeline import atualizar_status_transbordo
    atualizar_status_transbordo(db, empresa.id, telefone, None)
    return {"status": "ok", "mensagem": f"Robô reativado para {telefone}"}

@router.get("/config")
def get_config(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if not empresa.configuracoes:
        return {}
    return empresa.configuracoes.config

@router.put("/config")
def update_config(config_data: dict, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if empresa.configuracoes:
        empresa.configuracoes.config = config_data
    else:
        nova_config = Configuracao(empresa_id=empresa.id, config=config_data)
        db.add(nova_config)
    
    db.commit()
    return {"status": "ok", "mensagem": "Configurações atualizadas com sucesso"}
