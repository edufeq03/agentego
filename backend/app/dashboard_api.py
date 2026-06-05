from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database import (
    get_db, SessionLocal, Empresa, Lead, Mensagem, Evento, Configuracao, Usuario,
    MembroAcademia, CodigoRecuperacao, ClienteAgenciaViagens,
    ListaTransmissao, ListaTransmissaoContato, DisparoLista
)
from app.auth import verify_password, create_access_token, decode_access_token, get_password_hash
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
    # Limpa espaços em branco e faz busca case-insensitive
    email_clean = req.email.strip().lower()
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_clean).first()
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

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    import random
    from app.whatsapp import enviar_whatsapp
    
    email_clean = req.email.strip().lower()
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_clean).first()
    if not usuario:
        # Por segurança, retornamos 200 mesmo se o usuário não for encontrado para evitar enumeração de e-mails
        return {"status": "ok", "mensagem": "Código de recuperação enviado caso o e-mail esteja cadastrado."}
        
    # Gera código aleatório de 6 dígitos
    code = f"{random.randint(100000, 999999)}"
    expira_em = datetime.utcnow() + timedelta(minutes=15)
    
    # Invalida códigos antigos
    db.query(CodigoRecuperacao).filter(CodigoRecuperacao.usuario_id == usuario.id).delete()
    
    # Salva o novo código
    novo_codigo = CodigoRecuperacao(
        usuario_id=usuario.id,
        codigo=code,
        expira_em=expira_em
    )
    db.add(novo_codigo)
    db.commit()
    
    # Determina para qual número enviar o WhatsApp
    # Prioriza o telefone pessoal do proprietário, caso contrário envia para o whatsapp principal da empresa
    empresa = usuario.empresa
    destinatario = empresa.telefone_proprietario or empresa.telefone_whatsapp
    instance_name = empresa.evolution_instance or "agente-default"
    
    mensagem = (
        f"🔒 *Código de Recuperação - AgenteGo*\n\n"
        f"Olá! Você solicitou a redefinição de senha para o e-mail: *{usuario.email}*.\n\n"
        f"Seu código de verificação temporário é:\n"
        f"👉 *{code[0:3]} {code[3:6]}*\n\n"
        f"Este código expira em 15 minutos. Se você não solicitou esta redefinição, apenas desconsidere esta mensagem."
    )
    
    try:
        enviar_whatsapp(destinatario, mensagem, instance_name)
    except Exception as e:
        logger.error(f"Erro ao enviar código de recuperação via WhatsApp: {e}")
        # Mesmo se falhar o envio (ex: instância offline), não lançamos erro interno para o cliente
        
    return {"status": "ok", "mensagem": "Código de recuperação enviado com sucesso."}

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

@router.post("/verify-reset-code")
@limiter.limit("10/minute")
def verify_reset_code(request: Request, req: VerifyCodeRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    code_clean = req.code.strip().replace(" ", "")
    
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_clean).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="E-mail inválido ou código incorreto.")
        
    rec = db.query(CodigoRecuperacao).filter(
        CodigoRecuperacao.usuario_id == usuario.id,
        CodigoRecuperacao.codigo == code_clean
    ).first()
    
    if not rec:
        raise HTTPException(status_code=400, detail="Código incorreto.")
        
    if datetime.utcnow() > rec.expira_em:
        raise HTTPException(status_code=400, detail="Código expirado. Solicite um novo.")
        
    return {"status": "ok", "mensagem": "Código válido."}

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    code_clean = req.code.strip().replace(" ", "")
    
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_clean).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Operação inválida.")
        
    rec = db.query(CodigoRecuperacao).filter(
        CodigoRecuperacao.usuario_id == usuario.id,
        CodigoRecuperacao.codigo == code_clean
    ).first()
    
    if not rec:
        raise HTTPException(status_code=400, detail="Código inválido.")
        
    if datetime.utcnow() > rec.expira_em:
        raise HTTPException(status_code=400, detail="Código expirado. Solicite um novo.")
        
    # Atualiza a senha
    usuario.senha_hash = get_password_hash(req.new_password)
    
    # Invalida/deleta todos os códigos de recuperação do usuário
    db.query(CodigoRecuperacao).filter(CodigoRecuperacao.usuario_id == usuario.id).delete()
    
    db.commit()
    return {"status": "ok", "mensagem": "Senha redefinida com sucesso."}

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
    
    # Nicho Lanchonete: Metricas 100% customizadas e focadas em vendas/operacao
    if empresa.nicho == "lanchonete":
        from app.database import Pedido, ItemPedido, Transbordo
        
        # Total de pedidos (nao cancelados)
        total_pedidos = db.query(Pedido).filter(Pedido.empresa_id == empresa.id, Pedido.status != "cancelado").count()
        # Pedidos em preparo/fila
        pedidos_fila = db.query(Pedido).filter(Pedido.empresa_id == empresa.id, Pedido.status.in_(["aguardando", "em_preparo", "pronto"])).count()
        # Faturamento total
        faturamento_total = db.query(func.sum(Pedido.total)).filter(Pedido.empresa_id == empresa.id, Pedido.status != "cancelado").scalar() or 0.0
        # Ticket medio
        ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0.0
        # Mesas ativas (com pedidos em andamento)
        mesas_ativas = db.query(func.count(func.distinct(Pedido.numero_mesa))).filter(
            Pedido.empresa_id == empresa.id,
            Pedido.modo == "mesa",
            Pedido.status.in_(["aguardando", "em_preparo"])
        ).scalar() or 0
        
        # Transbordos pausados (aguardando humano)
        total_pausados = db.query(Transbordo).filter(Transbordo.empresa_id == empresa.id, Transbordo.status == "pausado").count()
        
        # Faturamento por dia (Ultimos 7 dias)
        faturamento_query = db.query(
            func.date(Pedido.criado_em).label('dia'),
            func.sum(Pedido.total).label('valor')
        ).filter(
            Pedido.empresa_id == empresa.id,
            Pedido.status != "cancelado",
            Pedido.criado_em >= limite_data
        ).group_by(func.date(Pedido.criado_em)).all()
        
        # Gerar os ultimos 7 dias deterministicos
        dias_dict = {(datetime.utcnow().date() - timedelta(days=i)): 0.0 for i in range(periodos_dias - 1, -1, -1)}
        for row in faturamento_query:
            if row.dia in dias_dict:
                dias_dict[row.dia] = row.valor
                
        grafico_conversas = [{"dia": str(dia), "mensagens": valor} for dia, valor in sorted(dias_dict.items())]
        
        # Distribuicao de Modos de Pedido (Delivery vs Mesa vs Balcao)
        modos_query = db.query(
            Pedido.modo,
            func.count(Pedido.id)
        ).filter(
            Pedido.empresa_id == empresa.id,
            Pedido.status != "cancelado"
        ).group_by(Pedido.modo).all()
        
        total_modos = sum(count for _, count in modos_query)
        dist_modos = {"delivery": 0, "mesa": 0, "balcao": 0}
        for modo, count in modos_query:
            if modo in dist_modos:
                dist_modos[modo] = round((count / total_modos * 100), 1) if total_modos > 0 else 0
                
        return {
            "nicho": "lanchonete",
            "cards": {
                "total_pedidos": total_pedidos,
                "pedidos_fila": pedidos_fila,
                "faturamento_total": round(faturamento_total, 2),
                "ticket_medio": round(ticket_medio, 2),
                "mesas_ativas": mesas_ativas,
                "pausados": total_pausados,
                "dist_delivery": dist_modos["delivery"],
                "dist_mesa": dist_modos["mesa"],
                "dist_balcao": dist_modos["balcao"]
            },
            "grafico_conversas": grafico_conversas
        }
        
    # Nichos Generico / Academia / Outros / Viagens: Fluxo padrao de leads
    total_leads = db.query(Lead).filter(Lead.empresa_id == empresa.id).count()
    leads_recentes = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.criado_em >= limite_data).count()
    
    if empresa.nicho == "agencia_viagens":
        leads_interessados = db.query(Lead).filter(
            Lead.empresa_id == empresa.id, 
            Lead.stage.in_(["interessado", "curioso"])
        ).count()
    else:
        leads_interessados = db.query(Lead).filter(
            Lead.empresa_id == empresa.id, 
            Lead.stage.in_(["interessado", "quente", "agendado"])
        ).count()
    
    visitas = db.query(Evento).filter(
        Evento.empresa_id == empresa.id,
        Evento.tipo.in_(["visita_aceita", "perguntou_visita"]),
        Evento.timestamp >= limite_data
    ).count()
    
    em_cotacao = db.query(Lead).filter(
        Lead.empresa_id == empresa.id,
        Lead.stage.in_(["quente", "agendado", "em_cotacao"])
    ).count()
    
    fechados = db.query(Lead).filter(
        Lead.empresa_id == empresa.id,
        Lead.stage.in_(["fechado", "concluido"])
    ).count()
    
    mensagens_query = db.query(
        func.date(Mensagem.timestamp).label('dia'),
        func.count(Mensagem.id).label('quantidade')
    ).filter(
        Mensagem.empresa_id == empresa.id,
        Mensagem.tipo == "usuario",
        Mensagem.timestamp >= limite_data
    ).group_by(func.date(Mensagem.timestamp)).all()
    
    dias_dict = {(datetime.utcnow().date() - timedelta(days=i)): 0 for i in range(periodos_dias - 1, -1, -1)}
    for row in mensagens_query:
        if row.dia in dias_dict:
            dias_dict[row.dia] = row.quantidade
            
    grafico_conversas = [{"dia": str(dia), "mensagens": qtd} for dia, qtd in sorted(dias_dict.items())]
    
    mensagens_recentes = db.query(Mensagem.timestamp).filter(
        Mensagem.empresa_id == empresa.id,
        Mensagem.tipo == "usuario",
        Mensagem.timestamp >= limite_data
    ).all()
    
    comercial = 0
    fora_comercial = 0
    tz = pytz.timezone('America/Sao_Paulo')
    
    for (ts,) in mensagens_recentes:
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        local_ts = ts.astimezone(tz)
        if local_ts.weekday() <= 4 and 8 <= local_ts.hour < 18:
            comercial += 1
        else:
            fora_comercial += 1
            
    total_msgs = comercial + fora_comercial
    pct_comercial = (comercial / total_msgs * 100) if total_msgs > 0 else 0
    pct_fora = (fora_comercial / total_msgs * 100) if total_msgs > 0 else 0
    
    from app.database import Transbordo
    total_pausados = db.query(Transbordo).filter(Transbordo.empresa_id == empresa.id, Transbordo.status == "pausado").count()
    
    return {
        "nicho": empresa.nicho or "generico",
        "cards": {
            "total_leads": total_leads,
            "leads_recentes": leads_recentes,
            "leads_interessados": leads_interessados,
            "visitas": visitas,
            "em_cotacao": em_cotacao,
            "fechados": fechados,
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
                "timestamp": ultima_msg.timestamp.isoformat() + "Z",
                "transbordo": status_transbordo,
                "dados_customizados": lead.dados_customizados
            })
            
    return resultado

@router.get("/conversas/{telefone}")
def historico_conversa(telefone: str, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
        
    mensagens = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.asc()).all()
    
    return [{"tipo": m.tipo, "mensagem": m.mensagem, "timestamp": m.timestamp.isoformat() + "Z"} for m in mensagens]

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
    config_data = dict(config_obj.config) if config_obj and config_obj.config else {}
    
    # Decriptografar a chave do ElevenLabs se existir
    from app.utils_crypto import decrypt_key
    if "elevenlabs_api_key" in config_data:
        config_data["elevenlabs_api_key"] = decrypt_key(config_data["elevenlabs_api_key"])
    
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
        config_data = dict(config_data)
        # Criptografar a chave do ElevenLabs antes de salvar
        from app.utils_crypto import encrypt_key
        if "elevenlabs_api_key" in config_data:
            config_data["elevenlabs_api_key"] = encrypt_key(config_data["elevenlabs_api_key"])
            
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
        
    # Busca configurações adicionais de telefone
    configuracao = empresa.configuracoes
    telefones_ignorados = []
    whatsapp_cozinha = ""
    if configuracao and configuracao.config:
        telefones_ignorados = configuracao.config.get("telefones_ignorados", [])
        whatsapp_cozinha = configuracao.config.get("whatsapp_cozinha", "")

    return {
        "status": status,
        "qrcode": qrcode,
        "instance": instance_name,
        "telefone_proprietario": empresa.telefone_proprietario or "",
        "telefones_ignorados": telefones_ignorados,
        "whatsapp_cozinha": whatsapp_cozinha,
        "whatsapp_consultor": (empresa.configuracoes.config or {}).get("whatsapp_consultor", "") if empresa.configuracoes else "",
        "nicho": empresa.nicho or "generico"
    }

class SaveWhatsappConfigRequest(BaseModel):
    telefone_proprietario: Optional[str] = None
    telefones_ignorados: Optional[List[str]] = None
    whatsapp_cozinha: Optional[str] = None
    whatsapp_consultor: Optional[str] = None

@router.post("/whatsapp/config")
def save_whatsapp_config(req: SaveWhatsappConfigRequest, empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    if req.telefone_proprietario is not None:
        empresa.telefone_proprietario = req.telefone_proprietario.strip()
    
    configuracao = empresa.configuracoes
    if not configuracao:
        configuracao = Configuracao(empresa_id=empresa.id, config={})
        db.add(configuracao)
        db.commit()
        db.refresh(configuracao)
        
    config_dict = dict(configuracao.config) if configuracao.config else {}
    
    if req.telefones_ignorados is not None:
        config_dict["telefones_ignorados"] = req.telefones_ignorados
        
    if req.whatsapp_cozinha is not None:
        config_dict["whatsapp_cozinha"] = req.whatsapp_cozinha.strip()

    if req.whatsapp_consultor is not None:
        config_dict["whatsapp_consultor"] = req.whatsapp_consultor.strip()
        
    configuracao.config = config_dict
    db.commit()
    return {"status": "ok", "mensagem": "Configurações de telefones salvas com sucesso!"}

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
            if empresa.nicho == "corretora":
                lead = db.query(Lead).filter(
                    Lead.empresa_id == empresa.id,
                    Lead.telefone == telefone
                ).first()
                if not lead:
                    lead = Lead(
                        empresa_id=empresa.id,
                        telefone=telefone,
                        nome=nome,
                        stage="primeiro_contato"
                    )
                    db.add(lead)
                    db.commit()
                    db.refresh(lead)
                else:
                    lead.nome = nome
                    
                lead_seg = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
                if not lead_seg:
                    lead_seg = LeadSeguro(
                        id=lead.id,
                        empresa_id=empresa.id,
                        telefone=telefone,
                        canal_entrada="csv",
                        tipo_seguro=plano or "saude",
                        stage=lead.stage
                    )
                    db.add(lead_seg)
                else:
                    lead_seg.tipo_seguro = plano or lead_seg.tipo_seguro
                
                db.commit()
                importados += 1
                continue

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
    if empresa.nicho == "corretora":
        from app.database import LeadSeguro
        leads = db.query(LeadSeguro).filter(LeadSeguro.empresa_id == empresa.id).order_by(LeadSeguro.criado_em.desc()).all()
        resultado = []
        for l in leads:
            lead = db.query(Lead).filter(Lead.id == l.id).first()
            nome = lead.nome if lead else None
            
            plano_nome = f"{str(l.tipo_seguro).capitalize() if l.tipo_seguro else 'Não inf.'}"
            if l.marca_modelo:
                plano_nome += f" ({l.marca_modelo})"
            elif l.plano_anterior_nome:
                plano_nome += f" ({l.plano_anterior_nome})"
                
            data_venc = l.atualizado_em or l.criado_em or datetime.utcnow()
            status = "vencendo" if l.docs_pendentes else "ativo"
            
            resultado.append({
                "id": str(l.id),
                "nome": nome or l.telefone or "Lead de Seguros",
                "telefone": l.telefone,
                "plano_nome": plano_nome,
                "data_vencimento": data_venc.strftime("%d/%m/%Y"),
                "dias_restantes": len(l.docs_pendentes) if l.docs_pendentes else 0,
                "status": status
            })
        return resultado

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
    if empresa.nicho == "corretora":
        from app.database import LeadSeguro, Evento, Mensagem
        lead_seg = db.query(LeadSeguro).filter(LeadSeguro.id == membro_id, LeadSeguro.empresa_id == empresa.id).first()
        if not lead_seg:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        db.query(Evento).filter(Evento.lead_id == membro_id).delete()
        db.query(Mensagem).filter(Mensagem.lead_id == membro_id).delete()
        db.query(LeadSeguro).filter(LeadSeguro.id == membro_id).delete()
        db.query(Lead).filter(Lead.id == membro_id).delete()
        db.commit()
        return {"status": "ok"}

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

        recipients = []
        if empresa.nicho == "corretora":
            from app.database import LeadSeguro, Lead
            leads = db.query(LeadSeguro).filter(LeadSeguro.empresa_id == empresa_id).all()
            for l in leads:
                lead = db.query(Lead).filter(Lead.id == l.id).first()
                recipients.append({
                    "telefone": l.telefone,
                    "nome": lead.nome if lead else (l.telefone or "Lead de Seguros")
                })
        elif empresa.nicho == "lanchonete":
            from app.database import Lead
            leads = db.query(Lead).filter(Lead.empresa_id == empresa_id).all()
            for l in leads:
                recipients.append({
                    "telefone": l.telefone,
                    "nome": l.nome or l.telefone or "Cliente"
                })
        else:
            from app.database import MembroAcademia
            membros = db.query(MembroAcademia).filter(
                MembroAcademia.empresa_id == empresa_id,
                MembroAcademia.ativo == True
            ).all()
            for m in membros:
                recipients.append({
                    "telefone": m.telefone,
                    "nome": m.nome
                })

        from app.whatsapp import enviar_whatsapp, enviar_imagem_whatsapp
        from app.database import ComunicadoLog, Comunicado
        import asyncio
        import random

        logger.info(f"Iniciando disparo em massa para empresa {empresa.nome} ({len(recipients)} contatos)")

        for rc in recipients:
            telefone_rec = rc["telefone"]
            try:
                final_image_url = imagem_url
                if imagem_url and imagem_url.startswith("/uploads/"):
                    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
                    final_image_url = f"{base_url}{imagem_url}"

                if final_image_url:
                    enviar_imagem_whatsapp(telefone_rec, final_image_url, mensagem, empresa.evolution_instance)
                else:
                    enviar_whatsapp(telefone_rec, mensagem, empresa.evolution_instance)
                
                # Log de sucesso
                if comunicado_id:
                    log = ComunicadoLog(comunicado_id=comunicado_id, telefone=telefone_rec, status="sucesso")
                    db.add(log)
                    db.query(Comunicado).filter(Comunicado.id == comunicado_id).update({
                        "enviados": Comunicado.enviados + 1
                    })
                    db.commit()

                # Delay dinâmico
                delay = 5 + random.uniform(0, 5)
                await asyncio.sleep(delay) 
            except Exception as e:
                logger.error(f"Erro ao enviar comunicado para {telefone_rec}: {e}")
                if comunicado_id:
                    log = ComunicadoLog(comunicado_id=comunicado_id, telefone=telefone_rec, status="erro", erro=str(e))
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
    from app.database import Comunicado
    if not req.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    
    # Conta membros ativos para o resumo de acordo com o nicho
    if empresa.nicho == "corretora":
        from app.database import LeadSeguro
        total = db.query(LeadSeguro).filter(LeadSeguro.empresa_id == empresa.id).count()
    elif empresa.nicho == "lanchonete":
        from app.database import Lead
        total = db.query(Lead).filter(Lead.empresa_id == empresa.id).count()
    else:
        from app.database import MembroAcademia
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

class CampanhaRequest(BaseModel):
    codigo_ref: str
    nome: str
    origem: str
    descricao: Optional[str] = None

@router.get("/marketing/campanhas")
async def listar_campanhas(empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    from app.database import Campanha, Lead
    
    campanhas = db.query(Campanha).filter(Campanha.empresa_id == empresa.id).order_by(Campanha.criado_em.desc()).all()
    
    resultado = []
    
    etapas = empresa.etapas_funil or ["novo", "curioso", "interessado", "agendado"]
    etapa_conversao = etapas[-1].lower() if etapas else "agendado"
    
    for c in campanhas:
        # Leads gerados por esta campanha
        total_leads = db.query(Lead).filter(
            Lead.empresa_id == empresa.id,
            Lead.utm_campaign == c.codigo_ref
        ).count()
        
        # Leads convertidos (estágio final)
        leads_convertidos = db.query(Lead).filter(
            Lead.empresa_id == empresa.id,
            Lead.utm_campaign == c.codigo_ref,
            Lead.stage.ilike(etapa_conversao)
        ).count()
        
        taxa_conversao = round((leads_convertidos / total_leads * 100), 1) if total_leads > 0 else 0.0
        
        resultado.append({
            "id": str(c.id),
            "codigo_ref": c.codigo_ref,
            "nome": c.nome,
            "origem": c.origem,
            "descricao": c.descricao,
            "criado_em": c.criado_em.isoformat() if c.criado_em else None,
            "leads_gerados": total_leads,
            "leads_convertidos": leads_convertidos,
            "taxa_conversao": taxa_conversao
        })
        
    return resultado

@router.post("/marketing/campanhas")
async def criar_campanha(
    req: CampanhaRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import Campanha
    
    codigo_limpo = req.codigo_ref.upper().strip()
    if not codigo_limpo:
        raise HTTPException(status_code=400, detail="Código de referência inválido")
        
    # Verificar se já existe campanha com este código
    existe = db.query(Campanha).filter(Campanha.codigo_ref == codigo_limpo).first()
    if existe:
        raise HTTPException(status_code=400, detail="Já existe uma campanha com este código de referência")
        
    nova = Campanha(
        empresa_id=empresa.id,
        codigo_ref=codigo_limpo,
        nome=req.nome.strip(),
        origem=req.origem.lower().strip(),
        descricao=req.descricao.strip() if req.descricao else None
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    
    return {"status": "ok", "campanha": {
        "id": str(nova.id),
        "codigo_ref": nova.codigo_ref,
        "nome": nova.nome,
        "origem": nova.origem,
        "descricao": nova.descricao
    }}

@router.delete("/marketing/campanhas/{campanha_id}")
async def excluir_campanha(
    campanha_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import Campanha
    campanha = db.query(Campanha).filter(
        Campanha.id == campanha_id,
        Campanha.empresa_id == empresa.id
    ).first()
    
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
        
    db.delete(campanha)
    db.commit()
    
    return {"status": "ok"}


# --- DYNAMIC TRIAGE FIELDS ENDPOINTS (SaaS Global) ---

from typing import Optional, List
from pydantic import BaseModel

class CampoCustomizadoRequest(BaseModel):
    chave: str
    label: str
    tipo: str = "texto" # texto, numero, booleano, opcao_unica
    obrigatorio: bool = False
    opcoes: Optional[List[str]] = None
    ordem: int = 0
    ativo: bool = True
    dependencias: Optional[dict] = None

@router.get("/marketing/triage/fields")
async def listar_campos_triagem(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import CampoCustomizado
    
    campos = db.query(CampoCustomizado).filter(
        CampoCustomizado.empresa_id == empresa.id
    ).order_by(CampoCustomizado.ordem.asc(), CampoCustomizado.criado_em.asc()).all()
    
    # Seeder automático por nicho se a empresa tem 0 campos cadastrados
    if len(campos) == 0:
        logger.info(f"Executando seeder automático de campos de triagem para empresa {empresa.nome} (Nicho: {empresa.nicho})")
        novos_campos = []
        if empresa.nicho == "corretora":
            novos_campos = [
                CampoCustomizado(empresa_id=empresa.id, chave="tipo_seguro", label="Tipo de Seguro", tipo="opcao_unica", opcoes=["Saúde / PME", "Odontológico", "Carro", "Moto"], obrigatorio=True, ordem=10),
                CampoCustomizado(empresa_id=empresa.id, chave="nome_segurado", label="Nome do Segurado", tipo="texto", obrigatorio=True, ordem=20),
                CampoCustomizado(empresa_id=empresa.id, chave="idade_segurado", label="Idade ou Nascimento", tipo="texto", obrigatorio=True, ordem=30),
                CampoCustomizado(empresa_id=empresa.id, chave="marca_modelo", label="Marca e Modelo do Veículo", tipo="texto", obrigatorio=False, ordem=40),
                CampoCustomizado(empresa_id=empresa.id, chave="ano_fabricacao", label="Ano de Fabricação", tipo="numero", obrigatorio=False, ordem=50),
                CampoCustomizado(empresa_id=empresa.id, chave="cep_pernoite", label="CEP de Pernoite", tipo="texto", obrigatorio=False, ordem=60),
                CampoCustomizado(empresa_id=empresa.id, chave="uso_veiculo", label="Uso do Veículo", tipo="opcao_unica", opcoes=["particular", "trabalho", "aplicativo"], obrigatorio=False, ordem=70),
                CampoCustomizado(empresa_id=empresa.id, chave="tem_garagem", label="Possui Garagem?", tipo="booleano", obrigatorio=False, ordem=80),
            ]
        elif empresa.nicho == "generico" or empresa.nicho == "academia":
            novos_campos = [
                CampoCustomizado(empresa_id=empresa.id, chave="nome_completo", label="Nome Completo", tipo="texto", obrigatorio=True, ordem=10),
                CampoCustomizado(empresa_id=empresa.id, chave="idade", label="Idade", tipo="texto", obrigatorio=True, ordem=20),
                CampoCustomizado(empresa_id=empresa.id, chave="objetivo", label="Objetivo do Treino", tipo="opcao_unica", opcoes=["Emagrecimento", "Ganho de Massa", "Condicionamento"], obrigatorio=False, ordem=30),
                CampoCustomizado(empresa_id=empresa.id, chave="frequencia", label="Frequência Pretendida", tipo="opcao_unica", opcoes=["1 a 2 dias", "3 a 4 dias", "5+ dias"], obrigatorio=False, ordem=40),
            ]
        else:
            # Qualquer outro nicho ou genérico
            novos_campos = [
                CampoCustomizado(empresa_id=empresa.id, chave="nome_completo", label="Nome Completo", tipo="texto", obrigatorio=True, ordem=10),
                CampoCustomizado(empresa_id=empresa.id, chave="objetivo_contato", label="Objetivo do Contato", tipo="texto", obrigatorio=True, ordem=20),
            ]
        
        for c in novos_campos:
            db.add(c)
        db.commit()
        
        # Consultar novamente
        campos = db.query(CampoCustomizado).filter(
            CampoCustomizado.empresa_id == empresa.id
        ).order_by(CampoCustomizado.ordem.asc(), CampoCustomizado.criado_em.asc()).all()
        
    return [{
        "id": str(c.id),
        "chave": c.chave,
        "label": c.label,
        "tipo": c.tipo,
        "obrigatorio": c.obrigatorio,
        "opcoes": c.opcoes,
        "ordem": c.ordem,
        "ativo": c.ativo,
        "dependencias": c.dependencias
    } for c in campos]

@router.post("/marketing/triage/fields")
async def criar_campo_triagem(
    req: CampoCustomizadoRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import CampoCustomizado
    
    chave_limpa = req.chave.lower().replace(" ", "_").strip()
    if not chave_limpa:
        raise HTTPException(status_code=400, detail="Chave inválida")
        
    # Verificar se já existe campo com esta chave para a empresa
    existe = db.query(CampoCustomizado).filter(
        CampoCustomizado.empresa_id == empresa.id,
        CampoCustomizado.chave == chave_limpa
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Já existe um campo cadastrado com esta chave")
        
    novo = CampoCustomizado(
        empresa_id=empresa.id,
        chave=chave_limpa,
        label=req.label.strip(),
        tipo=req.tipo,
        obrigatorio=req.obrigatorio,
        opcoes=req.opcoes,
        ordem=req.ordem,
        ativo=req.ativo,
        dependencias=req.dependencias
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    
    return {"status": "ok", "campo": {
        "id": str(novo.id),
        "chave": novo.chave,
        "label": novo.label,
        "tipo": novo.tipo,
        "obrigatorio": novo.obrigatorio,
        "opcoes": novo.opcoes,
        "ordem": novo.ordem,
        "ativo": novo.ativo,
        "dependencias": novo.dependencias
    }}

@router.put("/marketing/triage/fields/{field_id}")
async def atualizar_campo_triagem(
    field_id: uuid.UUID,
    req: CampoCustomizadoRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import CampoCustomizado
    
    campo = db.query(CampoCustomizado).filter(
        CampoCustomizado.id == field_id,
        CampoCustomizado.empresa_id == empresa.id
    ).first()
    
    if not campo:
        raise HTTPException(status_code=404, detail="Campo não encontrado")
        
    campo.label = req.label.strip()
    campo.tipo = req.tipo
    campo.obrigatorio = req.obrigatorio
    campo.opcoes = req.opcoes
    campo.ordem = req.ordem
    campo.ativo = req.ativo
    campo.dependencias = req.dependencias
    
    db.commit()
    return {"status": "ok"}

@router.delete("/marketing/triage/fields/{field_id}")
async def excluir_campo_triagem(
    field_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.database import CampoCustomizado
    campo = db.query(CampoCustomizado).filter(
        CampoCustomizado.id == field_id,
        CampoCustomizado.empresa_id == empresa.id
    ).first()
    
    if not campo:
        raise HTTPException(status_code=404, detail="Campo não encontrado")
        
    db.delete(campo)
    db.commit()
    return {"status": "ok"}


# --- SMART RE-ENGAGEMENT ENDPOINTS (SaaS Global) ---

class ReengagementStep(BaseModel):
    step: int
    delay_hours: float
    prompt: str

class ReengagementConfigRequest(BaseModel):
    reengagement_inactivity_enabled: bool = False
    reengagement_inactivity_steps: List[ReengagementStep] = []
    reengagement_pending_enabled: bool = False
    reengagement_pending_steps: List[ReengagementStep] = []

@router.get("/marketing/reengagement")
async def obter_configuracao_reengajamento(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
    config_dict = config_obj.config if config_obj else {}
    
    # Determinar fallbacks baseados no nicho
    if empresa.nicho == "corretora":
        default_inactivity_prompt = "Pergunte se o cliente ainda tem interesse e se restou alguma dúvida, mantendo o tom muito simpático e informal."
        default_pending_prompt = "Lembre o lead amigavelmente de que precisamos das informações pendentes ({campos_pendentes}) para prosseguir com a cotação do seu seguro."
    else:
        # Academia / Outros
        default_inactivity_prompt = "Pergunte gentilmente se o cliente ainda tem interesse nas nossas soluções e se quer agendar uma visita experimental."
        default_pending_prompt = "Lembre o lead amigavelmente de que precisamos do preenchimento das informações pendentes ({campos_pendentes}) para liberar seu acesso."

    # Processar passos de inatividade com fallback
    inact_steps = config_dict.get("reengagement_inactivity_steps")
    if not inact_steps:
        old_prompt = config_dict.get("reengagement_inactivity_prompt")
        old_delay = config_dict.get("reengagement_inactivity_delay_hours")
        if old_prompt is not None:
            inact_steps = [{"step": 1, "delay_hours": float(old_delay or 2), "prompt": old_prompt}]
        else:
            inact_steps = [{"step": 1, "delay_hours": 2.0, "prompt": default_inactivity_prompt}]

    # Processar passos de campos pendentes com fallback
    pend_steps = config_dict.get("reengagement_pending_steps")
    if not pend_steps:
        old_prompt = config_dict.get("reengagement_pending_prompt")
        old_delay = config_dict.get("reengagement_pending_delay_hours")
        if old_prompt is not None:
            pend_steps = [{"step": 1, "delay_hours": float(old_delay or 1), "prompt": old_prompt}]
        else:
            pend_steps = [{"step": 1, "delay_hours": 1.0, "prompt": default_pending_prompt}]

    return {
        "reengagement_inactivity_enabled": config_dict.get("reengagement_inactivity_enabled", False),
        "reengagement_inactivity_steps": inact_steps,
        
        "reengagement_pending_enabled": config_dict.get("reengagement_pending_enabled", False),
        "reengagement_pending_steps": pend_steps,
    }

@router.post("/marketing/reengagement")
async def atualizar_configuracao_reengajamento(
    req: ReengagementConfigRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm.attributes import flag_modified
    
    config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
    if not config_obj:
        config_obj = Configuracao(empresa_id=empresa.id, config={})
        db.add(config_obj)
        db.flush()
        
    config_dict = config_obj.config
    
    config_dict["reengagement_inactivity_enabled"] = req.reengagement_inactivity_enabled
    config_dict["reengagement_inactivity_steps"] = [step.dict() for step in req.reengagement_inactivity_steps]
    
    config_dict["reengagement_pending_enabled"] = req.reengagement_pending_enabled
    config_dict["reengagement_pending_steps"] = [step.dict() for step in req.reengagement_pending_steps]
    
    # Manter campos antigos sincronizados com o primeiro passo da esteira para retrocompatibilidade
    if len(req.reengagement_inactivity_steps) > 0:
        config_dict["reengagement_inactivity_delay_hours"] = int(req.reengagement_inactivity_steps[0].delay_hours)
        config_dict["reengagement_inactivity_prompt"] = req.reengagement_inactivity_steps[0].prompt
    if len(req.reengagement_pending_steps) > 0:
        config_dict["reengagement_pending_delay_hours"] = int(req.reengagement_pending_steps[0].delay_hours)
        config_dict["reengagement_pending_prompt"] = req.reengagement_pending_steps[0].prompt
        
    config_obj.config = config_dict
    flag_modified(config_obj, "config")
    db.commit()
    
    return {"status": "ok"}


# --- ENDPOINTS DO NICHO LANCHONETE ---

class CardapioItemRequest(BaseModel):
    categoria: str
    nome: str
    preco: float
    descricao: Optional[str] = None
    disponivel: bool = True
    ordem: int = 0

class PedidoStatusRequest(BaseModel):
    status: str

@router.get("/lanchonete/cardapio")
def api_listar_cardapio(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.cardapio_service import listar_itens
    return listar_itens(db, empresa.id)

@router.post("/lanchonete/cardapio")
def api_adicionar_item_cardapio(
    req: CardapioItemRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.cardapio_service import adicionar_item
    item = adicionar_item(
        db=db,
        empresa_id=empresa.id,
        categoria=req.categoria,
        nome=req.nome,
        preco=req.preco,
        descricao=req.descricao,
        disponivel=req.disponivel,
        ordem=req.ordem
    )
    return item

@router.put("/lanchonete/cardapio/{item_id}")
def api_atualizar_item_cardapio(
    item_id: uuid.UUID,
    req: CardapioItemRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.cardapio_service import atualizar_item
    item = atualizar_item(
        db=db,
        item_id=item_id,
        categoria=req.categoria,
        nome=req.nome,
        preco=req.preco,
        descricao=req.descricao,
        disponivel=req.disponivel,
        ordem=req.ordem
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no cardápio")
    return item

@router.patch("/lanchonete/cardapio/{item_id}/disponibilidade")
def api_toggle_disponibilidade_item(
    item_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.cardapio_service import toggle_disponibilidade
    item = toggle_disponibilidade(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no cardápio")
    return item

@router.delete("/lanchonete/cardapio/{item_id}")
def api_remover_item_cardapio(
    item_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.cardapio_service import remover_item
    sucesso = remover_item(db, item_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"status": "ok"}

@router.get("/lanchonete/pedidos/ativos")
def api_listar_pedidos_ativos(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.pedido_service import obter_pedidos_ativos
    pedidos = obter_pedidos_ativos(db, empresa.id)
    
    # Adicionar dados de resumo e nomes para simplificar o frontend
    resultado = []
    for ped in pedidos:
        cliente_nome = "Cliente"
        cliente_telefone = "Não inf."
        if ped.lead_id:
            lead = db.query(Lead).filter(Lead.id == ped.lead_id).first()
            if lead:
                cliente_nome = lead.nome or "Cliente"
                cliente_telefone = lead.telefone
                
        itens_list = []
        for it in ped.itens:
            itens_list.append({
                "id": str(it.id),
                "nome": it.nome,
                "preco_unit": it.preco_unit,
                "quantidade": it.quantidade,
                "observacao": it.observacao
            })
            
        resultado.append({
            "id": str(ped.id),
            "numero_pedido": ped.numero_pedido,
            "modo": ped.modo,
            "status": ped.status,
            "total": ped.total,
            "observacao": ped.observacao,
            "endereco": ped.endereco,
            "nome_balcao": ped.nome_balcao,
            "numero_mesa": ped.numero_mesa,
            "criado_em": ped.criado_em.isoformat() if ped.criado_em else None,
            "cliente": {
                "nome": cliente_nome,
                "telefone": cliente_telefone
            },
            "itens": itens_list
        })
    return resultado

@router.get("/lanchonete/pedidos/historico")
def api_listar_historico_pedidos(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.pedido_service import obter_historico_pedidos
    pedidos = obter_historico_pedidos(db, empresa.id, status=status, limit=limit, offset=offset)
    
    resultado = []
    for ped in pedidos:
        cliente_nome = "Cliente"
        cliente_telefone = "Não inf."
        if ped.lead_id:
            lead = db.query(Lead).filter(Lead.id == ped.lead_id).first()
            if lead:
                cliente_nome = lead.nome or "Cliente"
                cliente_telefone = lead.telefone
                
        itens_list = []
        for it in ped.itens:
            itens_list.append({
                "id": str(it.id),
                "nome": it.nome,
                "preco_unit": it.preco_unit,
                "quantidade": it.quantidade,
                "observacao": it.observacao
            })
            
        resultado.append({
            "id": str(ped.id),
            "numero_pedido": ped.numero_pedido,
            "modo": ped.modo,
            "status": ped.status,
            "total": ped.total,
            "observacao": ped.observacao,
            "endereco": ped.endereco,
            "nome_balcao": ped.nome_balcao,
            "numero_mesa": ped.numero_mesa,
            "criado_em": ped.criado_em.isoformat() if ped.criado_em else None,
            "cliente": {
                "nome": cliente_nome,
                "telefone": cliente_telefone
            },
            "itens": itens_list
        })
    return resultado

@router.patch("/lanchonete/pedidos/{pedido_id}/status")
def api_atualizar_status_pedido(
    pedido_id: uuid.UUID,
    req: PedidoStatusRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    from app.pedido_service import atualizar_status_pedido
    
    pedido = atualizar_status_pedido(db, pedido_id, req.status)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return {"status": "ok", "novo_status": pedido.status}

@router.get("/lanchonete/mesa/qrcode")
def api_gerar_qrcode_mesa(
    numero_mesa: int,
    empresa: Empresa = Depends(obter_empresa)
):
    # Gerar link com mensagem pre-preenchida para iniciar pedido na mesa
    telefone_empresa = empresa.telefone_whatsapp or ""
    telefone_limpo = "".join(filter(str.isdigit, str(telefone_empresa)))
    if not telefone_limpo:
        telefone_limpo = "5511999999999" # Fallback
        
    import urllib.parse
    mensagem = f"Olá, gostaria de fazer um pedido na Mesa {numero_mesa}"
    msg_encoded = urllib.parse.quote(mensagem)
    
    link_wa = f"https://wa.me/{telefone_limpo}?text={msg_encoded}"
    return {
        "numero_mesa": numero_mesa,
        "link_whatsapp": link_wa
    }


# =============================================================================
# NICHO: AGÊNCIA DE VIAGENS — Gestão de Clientes
# =============================================================================

class ClienteAgenciaRequest(BaseModel):
    nome: str
    telefone: str
    email: Optional[str] = None
    canal_entrada: str = "manual"
    destinos_interesse: Optional[List[str]] = None
    observacoes: Optional[str] = None

class ClienteAgenciaUpdateRequest(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    destinos_interesse: Optional[List[str]] = None
    observacoes: Optional[str] = None

@router.get("/agencia/clientes")
async def listar_clientes_agencia(
    search: Optional[str] = None,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Lista clientes da agência de viagens com busca opcional por nome/telefone."""
    query = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.empresa_id == empresa.id
    )
    if search:
        query = query.filter(
            (ClienteAgenciaViagens.nome.ilike(f"%{search}%")) |
            (ClienteAgenciaViagens.telefone.ilike(f"%{search}%"))
        )
    clientes = query.order_by(ClienteAgenciaViagens.criado_em.desc()).all()
    return [{
        "id": str(c.id),
        "nome": c.nome,
        "telefone": c.telefone,
        "email": c.email,
        "canal_entrada": c.canal_entrada,
        "destinos_interesse": c.destinos_interesse or [],
        "observacoes": c.observacoes,
        "criado_em": c.criado_em.isoformat() if c.criado_em else None,
        "atualizado_em": c.atualizado_em.isoformat() if c.atualizado_em else None,
    } for c in clientes]

@router.post("/agencia/clientes")
async def criar_cliente_agencia(
    req: ClienteAgenciaRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Cadastra manualmente um cliente da agência de viagens."""
    # Normaliza telefone
    tel = "".join(filter(str.isdigit, req.telefone))
    if len(tel) == 11:
        tel = "55" + tel

    # Verifica duplicata
    existente = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.empresa_id == empresa.id,
        ClienteAgenciaViagens.telefone == tel
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um cliente cadastrado com este telefone.")

    # Cria ou encontra o Lead correspondente
    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == tel).first()
    if not lead:
        lead = Lead(empresa_id=empresa.id, telefone=tel, nome=req.nome, stage="novo")
        db.add(lead)
        db.flush()

    novo = ClienteAgenciaViagens(
        empresa_id=empresa.id,
        lead_id=lead.id,
        nome=req.nome.strip(),
        telefone=tel,
        email=req.email.strip() if req.email else None,
        canal_entrada=req.canal_entrada,
        destinos_interesse=req.destinos_interesse or [],
        observacoes=req.observacoes,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"status": "ok", "id": str(novo.id)}

@router.put("/agencia/clientes/{cliente_id}")
async def atualizar_cliente_agencia(
    cliente_id: uuid.UUID,
    req: ClienteAgenciaUpdateRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Atualiza dados de um cliente da agência."""
    cliente = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.id == cliente_id,
        ClienteAgenciaViagens.empresa_id == empresa.id
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if req.nome is not None:
        cliente.nome = req.nome.strip()
    if req.email is not None:
        cliente.email = req.email.strip()
    if req.destinos_interesse is not None:
        cliente.destinos_interesse = req.destinos_interesse
    if req.observacoes is not None:
        cliente.observacoes = req.observacoes
    cliente.atualizado_em = datetime.utcnow()

    db.commit()
    return {"status": "ok"}

@router.delete("/agencia/clientes/{cliente_id}")
async def remover_cliente_agencia(
    cliente_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Remove um cliente da agência (não remove o Lead base)."""
    cliente = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.id == cliente_id,
        ClienteAgenciaViagens.empresa_id == empresa.id
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()
    return {"status": "ok"}

@router.get("/agencia/clientes/stats")
async def stats_clientes_agencia(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Estatísticas dos clientes da agência."""
    from datetime import date
    total = db.query(ClienteAgenciaViagens).filter(ClienteAgenciaViagens.empresa_id == empresa.id).count()
    hoje_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    novos_hoje = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.empresa_id == empresa.id,
        ClienteAgenciaViagens.criado_em >= hoje_inicio
    ).count()
    via_whatsapp = db.query(ClienteAgenciaViagens).filter(
        ClienteAgenciaViagens.empresa_id == empresa.id,
        ClienteAgenciaViagens.canal_entrada == "whatsapp"
    ).count()
    return {"total": total, "novos_hoje": novos_hoje, "via_whatsapp": via_whatsapp}


# =============================================================================
# MÓDULO INDEPENDENTE: LISTAS DE TRANSMISSÃO
# Habilitado por: nicho == 'agencia_viagens' OU 'listas_transmissao' em modulos_ativos
# =============================================================================

class ListaTransmissaoRequest(BaseModel):
    nome: str
    descricao: Optional[str] = None

class ContatoListaRequest(BaseModel):
    nome: Optional[str] = None
    telefone: str

class ContatosLoteRequest(BaseModel):
    """Para adicionar múltiplos contatos de uma vez (ex: importar dos clientes/leads)."""
    contatos: List[ContatoListaRequest]

class DisparoListaRequest(BaseModel):
    mensagem: str
    imagem_url: Optional[str] = None
    data_programada: Optional[datetime] = None

@router.get("/listas-transmissao")
async def listar_listas(
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Lista todas as listas de transmissão da empresa."""
    listas = db.query(ListaTransmissao).filter(
        ListaTransmissao.empresa_id == empresa.id
    ).order_by(ListaTransmissao.criado_em.desc()).all()

    resultado = []
    for lista in listas:
        total_contatos = db.query(ListaTransmissaoContato).filter(
            ListaTransmissaoContato.lista_id == lista.id
        ).count()
        ultimo_disparo = db.query(DisparoLista).filter(
            DisparoLista.lista_id == lista.id
        ).order_by(DisparoLista.criado_em.desc()).first()

        resultado.append({
            "id": str(lista.id),
            "nome": lista.nome,
            "descricao": lista.descricao,
            "total_contatos": total_contatos,
            "ultimo_disparo": ultimo_disparo.criado_em.isoformat() if ultimo_disparo else None,
            "criado_em": lista.criado_em.isoformat() if lista.criado_em else None,
        })
    return resultado

@router.post("/listas-transmissao")
async def criar_lista(
    req: ListaTransmissaoRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Cria uma nova lista de transmissão."""
    if not req.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da lista não pode ser vazio.")
    nova = ListaTransmissao(
        empresa_id=empresa.id,
        nome=req.nome.strip(),
        descricao=req.descricao.strip() if req.descricao else None,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return {"status": "ok", "id": str(nova.id), "nome": nova.nome}

@router.delete("/listas-transmissao/{lista_id}")
async def remover_lista(
    lista_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Remove uma lista e todos seus contatos/disparos."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")
    db.delete(lista)
    db.commit()
    return {"status": "ok"}

@router.get("/listas-transmissao/buscar-contatos")
def buscar_contatos_lista(q: str = Query("", min_length=2), empresa: Empresa = Depends(obter_empresa), db: Session = Depends(get_db)):
    """Busca contatos na base da empresa (Leads, Clientes ou Membros) pelo nome ou telefone."""
    query_str = f"%{q}%"
    resultados = []
    
    # 1. Busca na tabela genérica de Leads
    leads = db.query(Lead).filter(
        Lead.empresa_id == empresa.id,
        or_(Lead.nome.ilike(query_str), Lead.telefone.ilike(query_str))
    ).limit(10).all()
    for l in leads:
        resultados.append({"nome": l.nome or "Desconhecido", "telefone": l.telefone})
        
    # 2. Busca em Agência de Viagens (se for do nicho)
    if empresa.nicho == "agencia_viagens":
        clientes = db.query(ClienteAgenciaViagens).filter(
            ClienteAgenciaViagens.empresa_id == empresa.id,
            or_(ClienteAgenciaViagens.nome.ilike(query_str), ClienteAgenciaViagens.telefone.ilike(query_str))
        ).limit(10).all()
        for c in clientes:
            resultados.append({"nome": c.nome, "telefone": c.telefone})
            
    # 3. Busca em Academia (se for do nicho)
    if empresa.nicho == "academia":
        membros = db.query(MembroAcademia).filter(
            MembroAcademia.empresa_id == empresa.id,
            or_(MembroAcademia.nome.ilike(query_str), MembroAcademia.telefone.ilike(query_str))
        ).limit(10).all()
        for m in membros:
            if m.telefone:
                resultados.append({"nome": m.nome, "telefone": m.telefone})
                
    # Remove duplicados baseados no telefone
    unicos = {}
    for r in resultados:
        tel = r["telefone"]
        if tel and tel not in unicos:
            unicos[tel] = r
            
    # Retorna no máximo 15 resultados
    return list(unicos.values())[:15]

@router.get("/listas-transmissao/{lista_id}/contatos")
async def listar_contatos_lista(
    lista_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Lista os contatos de uma lista de transmissão."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    contatos = db.query(ListaTransmissaoContato).filter(
        ListaTransmissaoContato.lista_id == lista_id
    ).order_by(ListaTransmissaoContato.adicionado_em.desc()).all()

    return {
        "lista": {"id": str(lista.id), "nome": lista.nome, "descricao": lista.descricao},
        "contatos": [{
            "id": str(c.id),
            "nome": c.nome or "",
            "telefone": c.telefone,
            "adicionado_em": c.adicionado_em.isoformat() if c.adicionado_em else None,
        } for c in contatos]
    }

@router.post("/listas-transmissao/{lista_id}/contatos")
async def adicionar_contato_lista(
    lista_id: uuid.UUID,
    req: ContatoListaRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Adiciona um único contato a uma lista de transmissão."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    tel = "".join(filter(str.isdigit, req.telefone))
    if len(tel) == 11:
        tel = "55" + tel
    if len(tel) not in [12, 13]:
        raise HTTPException(status_code=400, detail=f"Telefone inválido: {req.telefone}")

    # Evita duplicatas na mesma lista
    existente = db.query(ListaTransmissaoContato).filter(
        ListaTransmissaoContato.lista_id == lista_id,
        ListaTransmissaoContato.telefone == tel
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Este contato já está na lista.")

    # Tenta pegar o nome do Lead se não fornecido
    nome_final = req.nome
    if not nome_final:
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == tel).first()
        if lead and lead.nome:
            nome_final = lead.nome

    novo = ListaTransmissaoContato(
        lista_id=lista_id,
        empresa_id=empresa.id,
        nome=nome_final,
        telefone=tel,
    )
    db.add(novo)
    db.commit()
    return {"status": "ok"}

@router.post("/listas-transmissao/{lista_id}/contatos/lote")
async def adicionar_contatos_lote(
    lista_id: uuid.UUID,
    req: ContatosLoteRequest,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Adiciona múltiplos contatos de uma vez (útil para importar clientes/leads)."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    adicionados = 0
    ignorados = 0
    for c in req.contatos:
        tel = "".join(filter(str.isdigit, c.telefone))
        if len(tel) == 11:
            tel = "55" + tel
        if len(tel) not in [12, 13]:
            ignorados += 1
            continue
        existente = db.query(ListaTransmissaoContato).filter(
            ListaTransmissaoContato.lista_id == lista_id,
            ListaTransmissaoContato.telefone == tel
        ).first()
        if existente:
            ignorados += 1
            continue
        db.add(ListaTransmissaoContato(
            lista_id=lista_id,
            empresa_id=empresa.id,
            nome=c.nome,
            telefone=tel,
        ))
        adicionados += 1

    db.commit()
    return {"status": "ok", "adicionados": adicionados, "ignorados": ignorados}

@router.delete("/listas-transmissao/{lista_id}/contatos/{contato_id}")
async def remover_contato_lista(
    lista_id: uuid.UUID,
    contato_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Remove um contato de uma lista de transmissão."""
    contato = db.query(ListaTransmissaoContato).filter(
        ListaTransmissaoContato.id == contato_id,
        ListaTransmissaoContato.lista_id == lista_id,
        ListaTransmissaoContato.empresa_id == empresa.id
    ).first()
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    db.delete(contato)
    db.commit()
    return {"status": "ok"}

async def _disparar_lista_background(
    empresa_id: uuid.UUID,
    lista_id: uuid.UUID,
    disparo_id: uuid.UUID,
    mensagem: str,
    imagem_url: Optional[str] = None
):
    """Dispara mensagens para todos os contatos de uma lista em background."""
    import asyncio
    import random
    from app.whatsapp import enviar_whatsapp, enviar_imagem_whatsapp

    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            return

        contatos = db.query(ListaTransmissaoContato).filter(
            ListaTransmissaoContato.lista_id == lista_id
        ).all()

        disparo = db.query(DisparoLista).filter(DisparoLista.id == disparo_id).first()
        if disparo:
            disparo.status = "enviando"
            db.commit()

        for contato in contatos:
            try:
                final_url = imagem_url
                if final_url and final_url.startswith("/uploads/"):
                    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
                    final_url = f"{base_url}{final_url}"

                if final_url:
                    enviar_imagem_whatsapp(contato.telefone, final_url, mensagem, empresa.evolution_instance)
                else:
                    enviar_whatsapp(contato.telefone, mensagem, empresa.evolution_instance)

                if disparo:
                    db.query(DisparoLista).filter(DisparoLista.id == disparo_id).update({
                        "enviados": DisparoLista.enviados + 1
                    })
                    db.commit()
            except Exception as e:
                logger.error(f"Erro ao enviar para {contato.telefone} na lista {lista_id}: {e}")
                if disparo:
                    db.query(DisparoLista).filter(DisparoLista.id == disparo_id).update({
                        "erros": DisparoLista.erros + 1
                    })
                    db.commit()

            delay = 5 + random.uniform(0, 5)
            await asyncio.sleep(delay)

        if disparo:
            db.query(DisparoLista).filter(DisparoLista.id == disparo_id).update({
                "status": "enviado",
                "enviado_em": datetime.utcnow()
            })
            db.commit()
    finally:
        db.close()

@router.post("/listas-transmissao/{lista_id}/disparar")
async def disparar_lista(
    lista_id: uuid.UUID,
    req: DisparoListaRequest,
    background_tasks: BackgroundTasks,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Dispara uma mensagem para todos os contatos de uma lista de transmissão."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    if not req.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia.")

    total = db.query(ListaTransmissaoContato).filter(
        ListaTransmissaoContato.lista_id == lista_id
    ).count()

    if total == 0:
        raise HTTPException(status_code=400, detail="A lista não possui contatos.")

    novo_disparo = DisparoLista(
        lista_id=lista_id,
        empresa_id=empresa.id,
        mensagem=req.mensagem,
        imagem_url=req.imagem_url,
        status="pendente",
        total_contatos=total,
        data_programada=req.data_programada
    )
    db.add(novo_disparo)
    db.commit()
    db.refresh(novo_disparo)

    if not req.data_programada:
        background_tasks.add_task(
            _disparar_lista_background,
            empresa.id, lista_id, novo_disparo.id, req.mensagem, req.imagem_url
        )

    return {"status": "ok", "disparo_id": str(novo_disparo.id), "total_contatos": total}

@router.get("/listas-transmissao/{lista_id}/disparos")
async def listar_disparos_lista(
    lista_id: uuid.UUID,
    empresa: Empresa = Depends(obter_empresa),
    db: Session = Depends(get_db)
):
    """Lista o histórico de disparos de uma lista de transmissão."""
    lista = db.query(ListaTransmissao).filter(
        ListaTransmissao.id == lista_id,
        ListaTransmissao.empresa_id == empresa.id
    ).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    disparos = db.query(DisparoLista).filter(
        DisparoLista.lista_id == lista_id
    ).order_by(DisparoLista.criado_em.desc()).all()

    return [{
        "id": str(d.id),
        "mensagem": d.mensagem,
        "imagem_url": d.imagem_url,
        "status": d.status,
        "total_contatos": d.total_contatos,
        "enviados": d.enviados,
        "erros": d.erros,
        "criado_em": d.criado_em.isoformat() if d.criado_em else None,
        "enviado_em": d.enviado_em.isoformat() if d.enviado_em else None,
    } for d in disparos]
