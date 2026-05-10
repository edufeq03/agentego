from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any
from pydantic import BaseModel

from app.database import get_db, Empresa, Lead, Mensagem, Evento, Configuracao, Usuario
from app.auth import verify_password, create_access_token, decode_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == req.email).first()
    if not usuario or not verify_password(req.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    
    # Verifica se a empresa está ativa
    if not usuario.empresa.ativo:
        raise HTTPException(status_code=403, detail="Empresa inativa")
        
    access_token = create_access_token(data={
        "sub": str(usuario.empresa_id),
        "role": usuario.role
    })
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "slug": usuario.empresa.slug
    }

def obter_empresa(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
    empresa_id = payload.get("sub")
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id, Empresa.ativo == True).first()
    
    if not empresa:
        raise HTTPException(status_code=401, detail="Empresa não encontrada ou inativa")
    
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
    
    # Visitas (eventos relacionados a visita)
    visitas = db.query(Evento).filter(
        Evento.empresa_id == empresa.id,
        Evento.tipo.in_(["visita_aceita", "perguntou_visita"]),
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
    
    # Cálculo Horário Comercial (Seg a Sex, 08h-18h)
    mensagens_recentes = db.query(Mensagem.timestamp).filter(
        Mensagem.empresa_id == empresa.id,
        Mensagem.tipo == "usuario",
        Mensagem.timestamp >= limite_data
    ).all()
    
    comercial = 0
    fora_comercial = 0
    tz = pytz.timezone('America/Sao_Paulo')
    
    for (ts,) in mensagens_recentes:
        # Converter para o fuso local
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        local_ts = ts.astimezone(tz)
        
        # 0 = Seg, 4 = Sex
        if local_ts.weekday() <= 4 and 8 <= local_ts.hour < 18:
            comercial += 1
        else:
            fora_comercial += 1
            
    total_msgs = comercial + fora_comercial
    pct_comercial = (comercial / total_msgs * 100) if total_msgs > 0 else 0
    pct_fora = (fora_comercial / total_msgs * 100) if total_msgs > 0 else 0
    
    return {
        "cards": {
            "total_leads": total_leads,
            "leads_recentes": leads_recentes,
            "leads_interessados": leads_interessados,
            "visitas": visitas,
            "horario_comercial_pct": round(pct_comercial, 1),
            "fora_horario_pct": round(pct_fora, 1),
            "total_mensagens_analisadas": total_msgs
        },
        "grafico_conversas": grafico_conversas
    }

@router.get("/funil")
def funil(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Usa as etapas dinâmicas da empresa
    etapas = empresa.etapas_funil or ["novo", "curioso", "interessado", "agendado"]
    
    # Contagem de leads por stage
    counts = db.query(Lead.stage, func.count(Lead.id)).filter(Lead.empresa_id == empresa.id).group_by(Lead.stage).all()
    counts_dict = {stage: count for stage, count in counts}
    
    grafico_funil = []
    colors = ["#8884d8", "#83a6ed", "#8dd1e1", "#82ca9d", "#a4de6c", "#d0ed57", "#ffc658"]
    
    for i, etapa in enumerate(etapas):
        # Para cada etapa, somamos ela e todas as seguintes (valor acumulado para o funil)
        valor = sum(counts_dict.get(e, 0) for e in etapas[i:])
        grafico_funil.append({
            "name": etapa.capitalize(),
            "value": valor,
            "fill": colors[i % len(colors)]
        })
            
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

import os

@router.get("/config")
def get_config(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Busca a configuração de forma explícita para evitar cache de relacionamento
    config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
    config_data = config_obj.config if config_obj else {}
    
    # DEBUG: Para vermos o que está saindo para o Dashboard
    print(f"DEBUG API -> Enviando config para {empresa.nome}: {config_data}")
    
    return {
        "config": config_data,
        "webhook_token": empresa.webhook_token,
        "base_url": os.getenv("BASE_URL", "http://localhost:8000")
    }

@router.put("/config")
def update_config(config_data: dict, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if empresa.configuracoes:
        empresa.configuracoes.config = config_data
    else:
        nova_config = Configuracao(empresa_id=empresa.id, config=config_data)
        db.add(nova_config)
    
    db.commit()
    return {"status": "ok", "mensagem": "Configurações atualizadas com sucesso"}
@router.post("/relatorio-semanal/enviar-agora")
async def disparar_relatorio_manual(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.reports import enviar_relatorio_semanal_empresa
    sucesso = await enviar_relatorio_semanal_empresa(db, empresa)
    if sucesso:
        return {"status": "ok", "mensagem": f"Relatório enviado com sucesso para {empresa.telefone_proprietario}"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar relatório. Verifique se o telefone do proprietário está configurado.")

# --- NOVOS ENDPOINTS: GESTÃO DE WHATSAPP (EVOLUTION API) ---
from app import whatsapp_service

from fastapi import BackgroundTasks

def sync_task_background(empresa_id: int):
    """Sincroniza as configurações da Evolution em segundo plano."""
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa or not empresa.evolution_instance:
            return
            
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        webhook_url = f"{base_url}/webhook/{empresa.webhook_token}"
        
        # Sincroniza Webhook e Configurações de Comportamento
        whatsapp_service.set_webhook(empresa.evolution_instance, webhook_url)
        whatsapp_service.update_settings(empresa.evolution_instance)
        logger.info(f"[{empresa.evolution_instance}] Auto-sincronização de background concluída.")
    except Exception as e:
        logger.error(f"Erro na sincronização de background: {e}")
    finally:
        db.close()

@router.get("/whatsapp/status")
def get_whatsapp_status(background_tasks: BackgroundTasks, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # 1. Garante que a empresa tenha um nome de instância vinculado
    if not empresa.evolution_instance:
        safe_name = "".join(filter(str.isalnum, empresa.nome.lower()))
        instance_name = f"inst-{safe_name}-{str(empresa.id)[:4]}"
        empresa.evolution_instance = instance_name
        db.commit()
        db.refresh(empresa)

    instance_name = empresa.evolution_instance
    status = whatsapp_service.get_connection_status(instance_name)
    
    if status == "not_found":
        whatsapp_service.create_instance(instance_name)
        status = "disconnected"

    qrcode = None
    if status != "connected":
        qrcode = whatsapp_service.get_qrcode(instance_name)
    else:
        # Se conectou, agenda a sincronização para rodar em background
        # (Isso evita travar o polling do frontend)
        background_tasks.add_task(sync_task_background, empresa.id)
        
    return {
        "status": status,
        "qrcode": qrcode,
        "instance": instance_name
    }

@router.post("/whatsapp/logout")
def logout_whatsapp(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if not empresa.evolution_instance:
        raise HTTPException(status_code=404, detail="Nenhuma instância vinculada")
        
    sucesso = whatsapp_service.logout_instance(empresa.evolution_instance)
    if sucesso:
        return {"status": "ok", "mensagem": "WhatsApp desconectado com sucesso"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao desconectar WhatsApp")

@router.post("/whatsapp/sync")
def sync_whatsapp_config(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if not empresa.evolution_instance:
        raise HTTPException(status_code=404, detail="Nenhuma instância vinculada")
        
    try:
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        webhook_url = f"{base_url}/webhook/{empresa.webhook_token}"
        
        # 1. Sincroniza Webhook
        w_sucesso, w_erro = whatsapp_service.set_webhook(empresa.evolution_instance, webhook_url)
        if not w_sucesso:
            raise Exception(f"Erro Webhook: {w_erro}")
        
        # 2. Sincroniza Comportamento (Rejeitar chamadas, etc)
        s_sucesso, s_erro = whatsapp_service.update_settings(empresa.evolution_instance)
        if not s_sucesso:
            raise Exception(f"Erro Configurações: {s_erro}")
        
        return {"status": "ok", "mensagem": "Configurações e comportamento sincronizados com sucesso!"}
            
    except Exception as e:
        print(f"ERRO NA SINCRONIZAÇÃO: {e}")
        raise HTTPException(status_code=400, detail=str(e))
