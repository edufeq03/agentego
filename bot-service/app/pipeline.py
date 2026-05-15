import pytz
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from app.database import SessionLocal, Empresa, Lead, Mensagem, Transbordo, Configuracao, DocumentoLegal
from app.classifier import classificar_intencao, calcular_stage
from app.agent import processar_mensagem_dinamica, processar_confirmacao_transbordo
from app.context import gerar_contexto_tempo
from app.events import registrar_evento

def limpar_tags(texto: str) -> str:
    for tag in ["[SUGERIR_TRANSBORDO]", "[CONFIRMAR_TRANSBORDO]", "[CANCELAR_TRANSBORDO]"]:
        texto = texto.replace(tag, "").strip()
    return texto

def carregar_lead(db, empresa_id, telefone):
    lead = db.query(Lead).filter(Lead.empresa_id == empresa_id, Lead.telefone == telefone).first()
    if not lead:
        lead = Lead(empresa_id=empresa_id, telefone=telefone)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        # Evento: iniciou_conversa
        registrar_evento(db, empresa_id, lead.id, "iniciou_conversa")
    return lead

def obter_status_transbordo(db, empresa_id, telefone):
    transbordo = db.query(Transbordo).filter(Transbordo.empresa_id == empresa_id, Transbordo.telefone == telefone).first()
    return transbordo.status if transbordo else None

def atualizar_status_transbordo(db, empresa_id, telefone, novo_status, lead_id=None):
    transbordo = db.query(Transbordo).filter(Transbordo.empresa_id == empresa_id, Transbordo.telefone == telefone).first()
    if transbordo:
        if novo_status is None:
            db.delete(transbordo)
            if lead_id: registrar_evento(db, empresa_id, lead_id, "transbordo_cancelado")
        else:
            transbordo.status = novo_status
            if lead_id: 
                tipo = "transbordo_confirmado" if novo_status == "pausado" else "transbordo_sugerido"
                registrar_evento(db, empresa_id, lead_id, tipo)
    elif novo_status is not None:
        novo = Transbordo(empresa_id=empresa_id, telefone=telefone, status=novo_status)
        db.add(novo)
        if lead_id:
            tipo = "transbordo_confirmado" if novo_status == "pausado" else "transbordo_sugerido"
            registrar_evento(db, empresa_id, lead_id, tipo)
    db.commit()

def processar_webhook(empresa: Empresa, telefone: str, mensagem_texto: str):
    db = SessionLocal()
    
    status_transbordo = obter_status_transbordo(db, empresa.id, telefone)
    
    if status_transbordo == "pausado":
        db.close()
        return {"status": "pausado", "motivo": "transbordo_ativo"}

    # --- CONTROLE DE USO (BILLING) ---
    # 1. Verifica reset mensal do contador
    agora = datetime.utcnow()
    if not empresa.data_reset_contador or agora >= empresa.data_reset_contador:
        empresa.conversas_mes_atual = 0
        # Próximo reset: 1º dia do próximo mês
        if agora.month == 12:
            empresa.data_reset_contador = datetime(agora.year + 1, 1, 1)
        else:
            empresa.data_reset_contador = datetime(agora.year, agora.month + 1, 1)
        db.commit()

    # 2. Verifica se o lead é novo no mês (contabiliza 1 conversa)
    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
    
    # Se o lead não existe ou foi criado antes do último reset, consideramos uma "conversa ativa" este mês
    # No Modelo A, contamos "leads ativos no mês"
    # Aqui usaremos uma lógica simplificada: se a última mensagem do lead foi antes do reset, ele conta como nova conversa
    ultima_msg = db.query(Mensagem).filter(Mensagem.lead_id == lead.id if lead else False).order_by(Mensagem.timestamp.desc()).first()
    if not lead or not ultima_msg or ultima_msg.timestamp < (empresa.data_reset_contador - timedelta(days=31)):
        # Só incrementa se não for ilimitado ou se estiver abaixo do limite
        if empresa.plano != "ilimitado" and empresa.conversas_mes_atual >= empresa.limite_conversas_mes:
            db.close()
            return {
                "status": "limite_atingido", 
                "resposta": "Olá! No momento nosso atendimento automático atingiu o limite mensal. Por favor, aguarde que um atendente humano falará com você em breve. 🙏"
            }
        empresa.conversas_mes_atual = (empresa.conversas_mes_atual or 0) + 1
        db.commit()

    if not lead:
        lead = carregar_lead(db, empresa.id, telefone)
    # ---------------------------------
    
    # Salva a mensagem recebida
    intencao = classificar_intencao(mensagem_texto)
    msg_user = Mensagem(empresa_id=empresa.id, lead_id=lead.id, tipo="usuario", mensagem=mensagem_texto, intencao=intencao)
    db.add(msg_user)
    db.commit()

    # Analisa sentimento (IA)
    from app.classifier import analisar_sentimento_ia
    sentimento, t_in, t_out = analisar_sentimento_ia(mensagem_texto)
    
    # Registra tokens do sentimento
    empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
    empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
    db.commit()
    
    if sentimento == "negativo":
        registrar_evento(db, empresa.id, lead.id, "sentimento_negativo", {"mensagem": mensagem_texto})
    elif sentimento == "positivo":
        registrar_evento(db, empresa.id, lead.id, "sentimento_positivo")

    # Atualiza o funil de vendas (stage) baseado nas etapas da empresa
    etapas_empresa = empresa.etapas_funil or ["novo", "curioso", "interessado", "agendado"]
    novo_stage = calcular_stage(lead.stage, intencao, etapas_empresa)
    if novo_stage != lead.stage:
        lead.stage = novo_stage
        db.commit()
        
    # Registra o evento de intenção
    registrar_evento(db, empresa.id, lead.id, f"perguntou_{intencao}" if intencao != "duvida" else "fez_pergunta")

    # Recuperar histórico recente (limitado a 6)
    historico_db = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).limit(6).all()
    historico = []
    for m in reversed(historico_db):
        role = "user" if m.tipo == "usuario" else "assistant"
        # Não adicionamos a mensagem que acabamos de receber porque ela já é passada para a IA separadamente
        if m.id != msg_user.id:
            historico.append({"role": role, "content": m.mensagem})

    configuracao = empresa.configuracoes.config if empresa.configuracoes else {}
    contexto_tempo = gerar_contexto_tempo(configuracao)
    
    # Injeta nicho e documentos no config para o Agente
    configuracao["nicho"] = empresa.nicho or "generico"
    if configuracao["nicho"] == "contabilidade":
        docs = db.query(DocumentoLegal).filter(DocumentoLegal.empresa_id == empresa.id, DocumentoLegal.ativo == True).all()
        configuracao["documentos"] = [{"titulo": d.titulo, "conteudo": d.conteudo} for d in docs]
    else:
        configuracao["documentos"] = []

    if status_transbordo == "aguardando":
        resposta_raw, t_in, t_out = processar_confirmacao_transbordo(mensagem_texto, historico=historico)
        if "[CONFIRMAR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, "pausado", lead_id=lead.id)
        elif "[CANCELAR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, None, lead_id=lead.id)
    else:
        resposta_raw, t_in, t_out = processar_mensagem_dinamica(mensagem_texto, configuracao, intencao, lead.stage, contexto_tempo, historico=historico, sentimento=sentimento)
        if "[SUGERIR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, "aguardando", lead_id=lead.id)

    # Registra tokens da resposta principal
    empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
    empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
    db.commit()

    resposta_limpa = limpar_tags(resposta_raw)
    logger.info(f"Resposta gerada para {telefone}", extra={"empresa_id": str(empresa.id), "lead_id": str(lead.id), "tipo": "ia_response"})

    msg_bot = Mensagem(empresa_id=empresa.id, lead_id=lead.id, tipo="agente", mensagem=resposta_limpa)
    db.add(msg_bot)
    db.commit()
    db.close()

    return {"status": "ok", "resposta": resposta_limpa}

