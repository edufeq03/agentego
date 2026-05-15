from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db, SessionLocal, Empresa, Lead, Mensagem, Evento, Configuracao, Usuario, MembroAcademia
from app.auth import verify_password, create_access_token, decode_access_token
import logging
import os
import csv
import io
import uuid
from dateutil import parser as dateparser
from app import whatsapp_service
from fastapi import BackgroundTasks
from app.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
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
        "slug": usuario.empresa.slug,
        "nicho": usuario.empresa.nicho or "generico"
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
    
    # Transbordos pausados (aguardando humano)
    from app.database import Transbordo
    total_pausados = db.query(Transbordo).filter(Transbordo.empresa_id == empresa.id, Transbordo.status == "pausado").count()
    
    return {
        "cards": {
            "total_leads": total_leads,
            "leads_recentes": leads_recentes,
            "leads_interessados": leads_interessados,
            "visitas": visitas,
            "pausados": total_pausados,
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
    
    # Contagem de leads por stage (normaliza para bater com as labels se necessário)
    counts = db.query(Lead.stage, func.count(Lead.id)).filter(Lead.empresa_id == empresa.id).group_by(Lead.stage).all()
    counts_dict = {str(stage).lower().strip(): count for stage, count in counts if stage}
    
    grafico_funil = []
    colors = ["#8884d8", "#83a6ed", "#8dd1e1", "#82ca9d", "#a4de6c", "#d0ed57", "#ffc658"]
    
    for i, etapa in enumerate(etapas):
        # Mapeamento inteligente: se a etapa for "Novo lead" e no banco estiver "novo", somamos.
        # Vamos buscar por correspondência de prefixo ou igualdade exata (normalizada)
        etapa_key = etapa.lower().strip()
        
        # Para o funil acumulado, somamos esta etapa e todas as posteriores
        valor = 0
        for e_posterior in etapas[i:]:
            e_post_key = e_posterior.lower().strip()
            # Soma se bater exatamente ou se a etapa do banco estiver contida na label (ex: "novo" em "novo lead")
            valor += sum(count for k, count in counts_dict.items() if k == e_post_key or k in e_post_key)
            
        grafico_funil.append({
            "name": etapa.capitalize() if " " not in etapa else etapa, # Mantém capitalização se tiver espaços
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

@router.post("/conversas/{telefone}/enviar")
def enviar_mensagem_humana(telefone: str, payload: dict, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.whatsapp import enviar_whatsapp
    from app.database import Mensagem, Lead
    
    mensagem_texto = payload.get("mensagem")
    if not mensagem_texto:
        raise HTTPException(status_code=400, detail="Mensagem vazia")
        
    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
        
    # 1. Enviar via WhatsApp
    enviar_whatsapp(telefone, mensagem_texto, empresa.evolution_instance)
    
    # 2. Salvar no histórico como 'agente' (ou 'humano', mas nosso sistema usa agente para o que sai do sistema)
    nova_msg = Mensagem(
        empresa_id=empresa.id,
        lead_id=lead.id,
        tipo="agente",
        mensagem=mensagem_texto
    )
    db.add(nova_msg)
    db.commit()
    
    return {"status": "ok", "mensagem": "Mensagem enviada"}



@router.get("/config")
def get_config(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    # Busca a configuração de forma explícita para evitar cache de relacionamento
    config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
    config_data = config_obj.config if config_obj else {}
    
    # Log apenas da ação, sem expor o conteúdo sensível de config_data em INFO
    logger.info(f"Config solicitada: Empresa={empresa.nome} ID={empresa.id} Telefone={empresa.telefone_proprietario}")
    logger.debug(f"Config enviada para {empresa.nome}")
    
    return {
        "config": config_data,
        "nome": empresa.nome,
        "plano": empresa.plano,
        "telefone_proprietario": empresa.telefone_proprietario,
        "webhook_token": empresa.webhook_token,
        "base_url": os.getenv("BASE_URL", "http://localhost:8000"),
        "nicho": empresa.nicho or "generico"
    }

@router.put("/config")
def update_config(payload: dict, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    config_data = payload.get("config")
    telefone = payload.get("telefone_proprietario")
    
    if config_data:
        if empresa.configuracoes:
            empresa.configuracoes.config = config_data
        else:
            nova_config = Configuracao(empresa_id=empresa.id, config=config_data)
            db.add(nova_config)
            
    if telefone is not None:
        empresa.telefone_proprietario = telefone
    
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


# Controle de sincronização em memória para evitar tarefas redundantes
# Formato: {instance_name: timestamp_da_ultima_sincronizacao}
ultima_sincronizacao = {}

def sync_task_background(empresa_id: Any):
    """Sincroniza as configurações da Evolution em segundo plano."""
    logger.info(f"Iniciando tarefa de sincronização de background para empresa ID: {empresa_id}")
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            logger.error(f"Empresa {empresa_id} não encontrada para sincronização.")
            return
        
        if not empresa.evolution_instance:
            logger.warning(f"Empresa {empresa.nome} ({empresa_id}) não possui instância vinculada.")
            return
            
        instance_name = empresa.evolution_instance
        base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
        webhook_url = f"{base_url}/webhook/{empresa.webhook_token}"
        
        logger.info(f"[{instance_name}] Sincronizando para URL de Webhook: {webhook_url}")
        
        # Sincroniza Webhook
        sucesso_wh, erro_wh = whatsapp_service.set_webhook(instance_name, webhook_url)
        if sucesso_wh:
            logger.info(f"[{instance_name}] Webhook sincronizado com SUCESSO.")
        else:
            logger.error(f"[{instance_name}] FALHA ao sincronizar Webhook: {erro_wh}")
        
        # Sincroniza Configurações de Comportamento
        logger.info(f"[{instance_name}] Sincronizando Configurações (RejectCall/GroupsIgnore/AlwaysOnline)")
        sucesso_st, erro_st = whatsapp_service.update_settings(instance_name)
        if sucesso_st:
            logger.info(f"[{instance_name}] Configurações sincronizadas com SUCESSO.")
        else:
            logger.error(f"[{instance_name}] FALHA ao sincronizar Configurações: {erro_st}")
        
        if sucesso_wh and sucesso_st:
            logger.info(f"[{instance_name}] Sincronização automática concluída com ÊXITO.")
            
    except Exception as e:
        logger.error(f"Erro CRÍTICO na sincronização de background para {empresa_id}: {e}", exc_info=True)
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
    
    qrcode = None
    if status != "connected" and status != "not_found":
        qrcode = whatsapp_service.get_qrcode(instance_name)
    elif status == "connected":
        # Só sincroniza se não foi sincronizado nos últimos 5 minutos
        agora = datetime.utcnow()
        last_sync = ultima_sincronizacao.get(instance_name)
        
        if not last_sync or (agora - last_sync) > timedelta(minutes=5):
            ultima_sincronizacao[instance_name] = agora
            background_tasks.add_task(sync_task_background, empresa.id)
            logger.info(f"[{instance_name}] Sincronização disparada via background task.")
        
    return {
        "status": status,
        "qrcode": qrcode,
        "instance": instance_name
    }

@router.post("/whatsapp/connect")
def connect_whatsapp(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if not empresa.evolution_instance:
        safe_name = "".join(filter(str.isalnum, empresa.nome.lower()))
        instance_name = f"inst-{safe_name}-{str(empresa.id)[:4]}"
        empresa.evolution_instance = instance_name
        db.commit()
        db.refresh(empresa)

    instance_name = empresa.evolution_instance
    status = whatsapp_service.get_connection_status(instance_name)
    
    if status == "not_found":
        success = whatsapp_service.create_instance(instance_name)
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao criar instância")
        return {"status": "created", "message": "Instância criada com sucesso."}
    
    return {"status": status, "message": "Instância já existente."}

@router.post("/whatsapp/logout")
def logout_whatsapp(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if not empresa.evolution_instance:
        raise HTTPException(status_code=404, detail="Nenhuma instância vinculada")
        
    sucesso = whatsapp_service.logout_instance(empresa.evolution_instance)
    if sucesso:
        # Remove do cache de sincronização para permitir nova sincronização ao reconectar
        if empresa.evolution_instance in ultima_sincronizacao:
            del ultima_sincronizacao[empresa.evolution_instance]
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
        logger.error(f"ERRO NA SINCRONIZAÇÃO: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS DE MEMBROS (NICHO ACADEMIA) ---

@router.post("/membros/importar-csv")
async def importar_membros_csv(
    file: UploadFile = File(...),
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv são aceitos")

    conteudo = await file.read()
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")
        
    reader = csv.DictReader(io.StringIO(texto))

    importados = 0
    erros = []

    for i, row in enumerate(reader):
        try:
            nome = row.get("nome") or row.get("Nome") or row.get("NOME")
            telefone_raw = row.get("celular") or row.get("telefone") or \
                           row.get("Celular") or row.get("Telefone")
            vencimento_raw = row.get("vencimento") or row.get("data_vencimento") or \
                             row.get("Vencimento") or row.get("Data Vencimento")
            plano = row.get("plano") or row.get("Plano") or None

            if not nome or not telefone_raw or not vencimento_raw:
                erros.append(f"Linha {i+2}: campos obrigatórios ausentes")
                continue

            # Normalizar telefone
            telefone = "".join(filter(str.isdigit, telefone_raw))
            if len(telefone) == 11:
                telefone = "55" + telefone
            if len(telefone) not in [12, 13]:
                erros.append(f"Linha {i+2}: telefone inválido ({telefone_raw})")
                continue

            # Parsear data
            try:
                data_venc = dateparser.parse(vencimento_raw, dayfirst=True)
            except Exception:
                erros.append(f"Linha {i+2}: data inválida ({vencimento_raw})")
                continue

            # Upsert
            membro = db.query(MembroAcademia).filter(
                MembroAcademia.empresa_id == empresa.id,
                MembroAcademia.telefone == telefone
            ).first()

            if membro:
                membro.nome = nome
                membro.data_vencimento = data_venc
                membro.plano_nome = plano
                membro.ativo = True
                membro.aviso_7_dias_enviado = False
                membro.aviso_3_dias_enviado = False
                membro.aviso_vencido_enviado = False
                membro.atualizado_em = datetime.utcnow()
            else:
                novo = MembroAcademia(
                    empresa_id=empresa.id,
                    nome=nome,
                    telefone=telefone,
                    data_vencimento=data_venc,
                    plano_nome=plano
                )
                db.add(novo)
                importados += 1

        except Exception as e:
            erros.append(f"Linha {i+2}: erro inesperado ({str(e)})")

    db.commit()
    return {
        "status": "ok",
        "importados": importados,
        "erros": erros,
        "total_linhas": i + 1 if 'i' in locals() else 0
    }

@router.get("/membros")
def listar_membros(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    membros = db.query(MembroAcademia).filter(
        MembroAcademia.empresa_id == empresa.id
    ).order_by(MembroAcademia.data_vencimento.asc()).all()

    agora = datetime.utcnow()
    resultado = []
    for m in membros:
        dias_restantes = (m.data_vencimento - agora).days
        resultado.append({
            "id": str(m.id),
            "nome": m.nome,
            "telefone": m.telefone,
            "plano_nome": m.plano_nome,
            "data_vencimento": m.data_vencimento.strftime("%d/%m/%Y"),
            "dias_restantes": dias_restantes,
            "status": "vencido" if dias_restantes < 0
                      else "vencendo" if dias_restantes <= 7
                      else "ativo"
        })
    return resultado

@router.delete("/membros/{membro_id}")
def remover_membro(
    membro_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    membro = db.query(MembroAcademia).filter(
        MembroAcademia.id == membro_id,
        MembroAcademia.empresa_id == empresa.id
    ).first()
    if not membro:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    db.delete(membro)
    db.commit()
    return {"status": "ok"}

# --- BROADCAST (NICHO ACADEMIA) ---

async def disparar_comunicado_background(empresa_id: uuid.UUID, mensagem: str, imagem_url: Optional[str] = None, comunicado_id: Optional[uuid.UUID] = None):
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa: return

        membros = db.query(MembroAcademia).filter(
            MembroAcademia.empresa_id == empresa_id,
            MembroAcademia.ativo == True
        ).all()

        from app.whatsapp import enviar_whatsapp, enviar_imagem_whatsapp
        from app.database import ComunicadoLog, Comunicado
        import asyncio
        import random

        logger.info(f"Iniciando disparo em massa para empresa {empresa.nome} ({len(membros)} membros)")

        for membro in membros:
            try:
                final_image_url = imagem_url
                if imagem_url and imagem_url.startswith("/uploads/"):
                    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
                    final_image_url = f"{base_url}{imagem_url}"

                if final_image_url:
                    enviar_imagem_whatsapp(membro.telefone, final_image_url, mensagem, empresa.evolution_instance)
                else:
                    enviar_whatsapp(membro.telefone, mensagem, empresa.evolution_instance)
                
                # Log de sucesso
                if comunicado_id:
                    log = ComunicadoLog(comunicado_id=comunicado_id, telefone=membro.telefone, status="sucesso")
                    db.add(log)
                    db.query(Comunicado).filter(Comunicado.id == comunicado_id).update({
                        "enviados": Comunicado.enviados + 1
                    })
                    db.commit()

                # Delay dinâmico
                delay = 5 + random.uniform(0, 5)
                await asyncio.sleep(delay) 
            except Exception as e:
                logger.error(f"Erro ao enviar comunicado para {membro.telefone}: {e}")
                if comunicado_id:
                    log = ComunicadoLog(comunicado_id=comunicado_id, telefone=membro.telefone, status="erro", erro=str(e))
                    db.add(log)
                    db.query(Comunicado).filter(Comunicado.id == comunicado_id).update({
                        "erros": Comunicado.erros + 1
                    })
                    db.commit()
    finally:
        db.close()

class ComunicadoRequest(BaseModel):
    mensagem: str
    imagem_url: Optional[str] = None
    data_programada: Optional[datetime] = None

@router.get("/comunicados")
async def listar_comunicados(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.database import Comunicado
    return db.query(Comunicado).filter(Comunicado.empresa_id == empresa.id).order_by(Comunicado.criado_em.desc()).all()

@router.post("/comunicados/enviar")
async def criar_comunicado(
    req: ComunicadoRequest,
    background_tasks: BackgroundTasks,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import Comunicado, MembroAcademia
    if not req.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    
    # Conta membros ativos para o resumo
    total = db.query(MembroAcademia).filter(MembroAcademia.empresa_id == empresa.id, MembroAcademia.ativo == True).count()

    novo = Comunicado(
        empresa_id=empresa.id,
        mensagem=req.mensagem,
        imagem_url=req.imagem_url,
        data_programada=req.data_programada,
        status="pendente" if req.data_programada else "enviado", # Se não tem data, assume que vai enviar agora
        total_membros=total
    )
    db.add(novo)
    db.commit()

    if not req.data_programada:
        # Disparo imediato em background
        background_tasks.add_task(disparar_comunicado_background, empresa.id, req.mensagem, req.imagem_url, novo.id)
    
    return {"status": "ok", "message": "Comunicado agendado/enviado com sucesso."}

@router.get("/comunicados/{comunicado_id}/logs")
async def listar_logs_comunicado(
    comunicado_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import ComunicadoLog, Comunicado
    com = db.query(Comunicado).filter(Comunicado.id == comunicado_id, Comunicado.empresa_id == empresa.id).first()
    if not com:
        raise HTTPException(status_code=404, detail="Não encontrado")
    
    return db.query(ComunicadoLog).filter(ComunicadoLog.comunicado_id == comunicado_id).order_by(ComunicadoLog.criado_em.asc()).all()

@router.post("/upload")
async def upload_arquivo(
    file: UploadFile = File(...),
    empresa: Empresa = Depends(obter_empresa)
):
    # Pasta de uploads
    upload_dir = "app/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado")
        
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # Retorna a URL baseada no host da requisição (assumindo que o bot serve static)
    # Em produção, isso pode precisar de ajuste dependendo do reverse proxy
    # Vamos retornar um caminho relativo ou tentar deduzir a URL base
    return {"status": "ok", "url": f"/uploads/{filename}"}

@router.delete("/comunicados/{comunicado_id}")
async def excluir_comunicado(
    comunicado_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import Comunicado
    com = db.query(Comunicado).filter(Comunicado.id == comunicado_id, Comunicado.empresa_id == empresa.id).first()
    if not com:
        raise HTTPException(status_code=404, detail="Não encontrado")
    
    if com.status == "enviando":
        raise HTTPException(status_code=400, detail="Não é possível excluir um disparo em andamento")
        
    db.delete(com)
    db.commit()
    return {"status": "ok"}
