from datetime import datetime
import pytz
from app.database import get_db, Empresa, Lead, Mensagem, Evento, Transbordo, Configuracao
from app.classifier import classificar_intencao, calcular_stage
from app.agent import processar_mensagem_dinamica, processar_confirmacao_transbordo

def gerar_contexto_tempo():
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_str = dias_semana[agora.weekday()]
    hora_str = agora.strftime("%H:%M")
    return f"Hoje é {dia_str}, e a hora atual é {hora_str}."

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
    return lead

def obter_status_transbordo(db, empresa_id, telefone):
    transbordo = db.query(Transbordo).filter(Transbordo.empresa_id == empresa_id, Transbordo.telefone == telefone).first()
    return transbordo.status if transbordo else None

def atualizar_status_transbordo(db, empresa_id, telefone, novo_status):
    transbordo = db.query(Transbordo).filter(Transbordo.empresa_id == empresa_id, Transbordo.telefone == telefone).first()
    if transbordo:
        if novo_status is None:
            db.delete(transbordo)
        else:
            transbordo.status = novo_status
    elif novo_status is not None:
        novo = Transbordo(empresa_id=empresa_id, telefone=telefone, status=novo_status)
        db.add(novo)
    db.commit()

def processar_webhook(empresa: Empresa, telefone: str, mensagem_texto: str):
    db = get_db()
    
    status_transbordo = obter_status_transbordo(db, empresa.id, telefone)
    
    if status_transbordo == "pausado":
        db.close()
        return {"status": "pausado", "motivo": "transbordo_ativo"}

    lead = carregar_lead(db, empresa.id, telefone)
    
    # Salva a mensagem recebida
    intencao = classificar_intencao(mensagem_texto)
    msg_user = Mensagem(empresa_id=empresa.id, lead_id=lead.id, tipo="usuario", mensagem=mensagem_texto, intencao=intencao)
    db.add(msg_user)
    db.commit()

    # Atualiza o funil de vendas (stage)
    novo_stage = calcular_stage(lead.stage, intencao)
    if novo_stage != lead.stage:
        lead.stage = novo_stage
        db.commit()
        
    # Registra o evento
    evento = Evento(empresa_id=empresa.id, lead_id=lead.id, tipo=f"intencao_{intencao}")
    db.add(evento)
    db.commit()

    # Recuperar histórico recente (limitado a 6)
    historico_db = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).limit(6).all()
    historico = []
    for m in reversed(historico_db):
        role = "user" if m.tipo == "usuario" else "assistant"
        # Não adicionamos a mensagem que acabamos de receber porque ela já é passada para a IA separadamente
        if m.id != msg_user.id:
            historico.append({"role": role, "content": m.mensagem})

    contexto_tempo = gerar_contexto_tempo()
    configuracao = empresa.configuracoes.config if empresa.configuracoes else {}

    if status_transbordo == "aguardando":
        resposta_raw = processar_confirmacao_transbordo(mensagem_texto, historico=historico)
        if "[CONFIRMAR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, "pausado")
        elif "[CANCELAR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, None)
    else:
        resposta_raw = processar_mensagem_dinamica(mensagem_texto, configuracao, intencao, lead.stage, contexto_tempo, historico=historico)
        if "[SUGERIR_TRANSBORDO]" in resposta_raw:
            atualizar_status_transbordo(db, empresa.id, telefone, "aguardando")

    resposta_limpa = limpar_tags(resposta_raw)

    msg_bot = Mensagem(empresa_id=empresa.id, lead_id=lead.id, tipo="agente", mensagem=resposta_limpa)
    db.add(msg_bot)
    db.commit()
    db.close()

    return {"status": "ok", "resposta": resposta_limpa}
