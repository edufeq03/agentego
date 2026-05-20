import pytz
import logging
import re
import json
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from app.database import SessionLocal, Empresa, Lead, Mensagem, Transbordo, Configuracao, DocumentoLegal, LeadSeguro, DocumentoSeguro, FollowupSeguro
from app.classifier import classificar_intencao, calcular_stage
from app.agent import processar_mensagem_dinamica, processar_confirmacao_transbordo
from app.context import gerar_contexto_tempo
from app.events import registrar_evento
from app.seguro_template_parser import parsear_template_via_ia
from app.whatsapp import enviar_whatsapp

def limpar_tags(texto: str) -> str:
    for tag in ["[SUGERIR_TRANSBORDO]", "[CONFIRMAR_TRANSBORDO]", "[CANCELAR_TRANSBORDO]"]:
        texto = texto.replace(tag, "").strip()
    texto = re.sub(r'\[ATUALIZAR_LEAD:[^\]]*\]', '', texto)
    texto = re.sub(r'\[SOLICITAR_HUMANO:[^\]]*\]', '', texto)
    texto = re.sub(r'\[DOCUMENTO_RECEBIDO:[^\]]*\]', '', texto)
    texto = re.sub(r'\[ALERTA_ESFRIAMENTO[^\]]*\]', '', texto)
    return texto.strip()

def detectar_template_seguro(texto: str) -> bool:
    texto_lower = texto.lower()
    return (
        "contato:" in texto_lower and
        "nome:" in texto_lower and
        any(x in texto_lower for x in ["cotação", "cotacao", "seguro", "solicitando"])
    )

def calcular_docs_pendentes(tipo_seguro: str) -> list:
    if not tipo_seguro:
        return []
    tipo = tipo_seguro.lower()
    if tipo == "saude":
        return ["cnh_ou_rg"]
    elif tipo in ("auto", "moto"):
        return ["cnh", "crlv"]
    elif tipo == "residencial":
        return ["comprovante_residencia"]
    return []

def formatar_dados_lead(lead_seguro):
    if not lead_seguro:
        return "Nenhum dado coletado ainda."
    
    dados = []
    if lead_seguro.nome_segurado:
        dados.append(f"- Nome do Segurado: {lead_seguro.nome_segurado}")
    if lead_seguro.tipo_seguro:
        dados.append(f"- Tipo de Seguro de interesse: {lead_seguro.tipo_seguro.upper()}")
    if lead_seguro.produto_especifico:
        dados.append(f"- Produto Específico: {lead_seguro.produto_especifico}")
    if lead_seguro.relacao_segurado:
        dados.append(f"- Relação com o segurado: {lead_seguro.relacao_segurado}")
    if lead_seguro.idade_segurado:
        dados.append(f"- Idade do Segurado: {lead_seguro.idade_segurado}")
    if lead_seguro.tem_cnpj is not None:
        dados.append(f"- Possui CNPJ? {'Sim' if lead_seguro.tem_cnpj else 'Não'}")
    if lead_seguro.e_mei is not None:
        dados.append(f"- É MEI? {'Sim' if lead_seguro.e_mei else 'Não'}")
    if lead_seguro.tem_plano_anterior is not None:
        dados.append(f"- Plano Anterior? {'Sim' if lead_seguro.tem_plano_anterior else 'Não'}")
        if lead_seguro.plano_anterior_nome:
            dados.append(f"  - Nome do Plano Anterior: {lead_seguro.plano_anterior_nome}")
    if lead_seguro.mais_de_6_meses is not None:
        dados.append(f"- Sem plano há mais de 6 meses? {'Sim' if lead_seguro.mais_de_6_meses else 'Não'}")
    if lead_seguro.regiao:
        dados.append(f"- Região/Cidade: {lead_seguro.regiao}")
    if lead_seguro.hospitais_preferidos:
        dados.append(f"- Hospitais Preferidos: {lead_seguro.hospitais_preferidos}")
        
    # Auto/Moto details
    if lead_seguro.marca_modelo:
        dados.append(f"- Veículo (Marca/Modelo): {lead_seguro.marca_modelo}")
    if lead_seguro.ano_fabricacao:
        dados.append(f"- Ano de Fabricação: {lead_seguro.ano_fabricacao}")
    if lead_seguro.ano_modelo:
        dados.append(f"- Ano do Modelo: {lead_seguro.ano_modelo}")
    if lead_seguro.placa:
        dados.append(f"- Placa do Veículo: {lead_seguro.placa}")
    if lead_seguro.cep_pernoite:
        dados.append(f"- CEP de Pernoite: {lead_seguro.cep_pernoite}")
    if lead_seguro.uso_veiculo:
        dados.append(f"- Uso do Veículo: {lead_seguro.uso_veiculo}")
    if lead_seguro.tem_garagem is not None:
        dados.append(f"- Tem Garagem? {'Sim' if lead_seguro.tem_garagem else 'Não'}")
    if lead_seguro.condutor_principal:
        dados.append(f"- Condutor Principal: {lead_seguro.condutor_principal}")
    if lead_seguro.idade_condutor:
        dados.append(f"- Idade do Condutor: {lead_seguro.idade_condutor}")
    if lead_seguro.bonus_classe is not None:
        dados.append(f"- Classe de Bônus: {lead_seguro.bonus_classe}")
        
    return "\n".join(dados) if dados else "Nenhum dado cadastrado."

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
    
    # 1. Detectar template Piccolo Seguros se a empresa for corretora
    if empresa.nicho == "corretora" and detectar_template_seguro(mensagem_texto):
        logger.info("Template da Piccolo Seguros detectado! Iniciando extração e Modo A.")
        try:
            # Parsear template via IA
            data = parsear_template_via_ia(mensagem_texto)
            tel_lead = "".join(filter(str.isdigit, data.get("telefone", "")))
            if not tel_lead:
                tel_lead = "".join(filter(str.isdigit, telefone)) # fallback
            if len(tel_lead) == 11:
                tel_lead = "55" + tel_lead
                
            # Criar Lead base (upsert)
            lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == tel_lead).first()
            if not lead:
                lead = Lead(empresa_id=empresa.id, telefone=tel_lead, stage="primeiro_contato")
                db.add(lead)
                db.commit()
                db.refresh(lead)
                registrar_evento(db, empresa.id, lead.id, "iniciou_conversa")
            else:
                lead.stage = "primeiro_contato"
                db.commit()
                
            lead.nome = data.get("nome_contato") or data.get("nome_segurado") or lead.nome
            db.commit()
            
            # Criar ou atualizar LeadSeguro
            lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
            if not lead_seguro:
                lead_seguro = LeadSeguro(
                    id=lead.id,
                    empresa_id=empresa.id,
                    telefone=tel_lead,
                    canal_entrada="template",
                    template_raw=mensagem_texto,
                    stage="primeiro_contato"
                )
                db.add(lead_seguro)
            else:
                lead_seguro.canal_entrada = "template"
                lead_seguro.template_raw = mensagem_texto
                lead_seguro.stage = "primeiro_contato"
            
            # Salvar campos parseados do JSON
            print(f"DEBUG PIPELINE: data parseada da IA = {data}")
            for k, v in data.items():
                if hasattr(lead_seguro, k) and v is not None:
                    print(f"DEBUG PIPELINE: definindo {k} = {v}")
                    setattr(lead_seguro, k, v)
                    
            lead_seguro.docs_pendentes = calcular_docs_pendentes(data.get("tipo_seguro"))
            db.commit()
            
            # Salva o template recebido como mensagem do usuário no lead do cliente
            msg_user_template = Mensagem(
                empresa_id=empresa.id,
                lead_id=lead.id,
                tipo="usuario",
                mensagem=f"[Template Piccolo]: {mensagem_texto}",
                intencao="preco"
            )
            db.add(msg_user_template)
            db.commit()
            
            # Compor e enviar mensagem de boas-vindas
            config = empresa.configuracoes.config if empresa.configuracoes else {}
            nome_agente = config.get("nome_agente", "Rosana")
            nome_empresa = config.get("nome_empresa", empresa.nome)
            nome_cliente = (data.get("nome_contato") or "Olá").split()[0]
            
            produto = data.get("produto_especifico")
            tipo_seguro = data.get("tipo_seguro", "saude")
            mapa_tipo = {
                "saude": "Plano de Saúde",
                "odontologico": "Plano Odontológico",
                "auto": "Seguro Auto",
                "moto": "Seguro de Moto",
                "residencial": "Seguro Residencial",
            }
            produto_str = produto or mapa_tipo.get(tipo_seguro, "seguro")
            
            saudacao = f"Olá, *{nome_cliente}*! 👋"
            apresentacao = f"Sou o(a) *{nome_agente}*, assistente virtual da *{nome_empresa}*."
            corpo = (
                f"Recebi sua solicitação de cotação para *{produto_str}* e já estou com suas informações aqui. 😊\n\n"
                f"Em breve nossa equipe vai entrar em contato com as melhores opções para você.\n\n"
                f"Enquanto isso, posso te ajudar com qualquer dúvida sobre coberturas, carências ou funcionamento do plano. É só perguntar!"
            )
            
            campos_pendentes = data.get("campos_nao_informados", [])
            if campos_pendentes and tipo_seguro == "saude":
                if any("mei" in c.lower() or "cnpj" in c.lower() for c in campos_pendentes):
                    corpo += "\n\nPreciso de uma informação rápida: você possui CNPJ ou é MEI? Isso pode mudar as opções disponíveis para você."
                    
            mensagem_inicial = f"{saudacao}\n\n{apresentacao}\n\n{corpo}"
            
            # Enviar WhatsApp via Evolution API
            enviar_whatsapp(tel_lead, mensagem_inicial, empresa.evolution_instance)
            
            # Salvar mensagem enviada
            msg_bot = Mensagem(
                empresa_id=empresa.id,
                lead_id=lead.id,
                tipo="agente",
                mensagem=mensagem_inicial
            )
            db.add(msg_bot)
            db.commit()
            
            db.close()
            return {"status": "ok", "resposta": mensagem_inicial}
        except Exception as ex:
            logger.error(f"Erro ao processar template Piccolo: {ex}")
            # fall through to normal execution if error

    configuracao = empresa.configuracoes.config if empresa.configuracoes else {}
    telefones_ignorados = configuracao.get('telefones_ignorados', [])
    
    # Normaliza o telefone recebido (remove caracteres não numéricos)
    tel_limpo = "".join(filter(str.isdigit, telefone))
    
    if tel_limpo in telefones_ignorados or telefone in telefones_ignorados:
        logger.info(f"Mensagem de {telefone} ignorada (Blacklist)")
        db.close()
        return {"status": "ignorado", "motivo": "blacklist"}

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
    
    if empresa.nicho == "corretora" and lead:
        lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
        if not lead_seguro:
            lead_seguro = LeadSeguro(
                id=lead.id,
                empresa_id=empresa.id,
                telefone=lead.telefone,
                canal_entrada="organico",
                stage=lead.stage
            )
            db.add(lead_seguro)
            db.commit()
    
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
    elif configuracao["nicho"] == "corretora":
        lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
        configuracao["dados_lead"] = formatar_dados_lead(lead_seguro)
        configuracao["docs_pendentes"] = ", ".join(lead_seguro.docs_pendentes) if (lead_seguro and lead_seguro.docs_pendentes) else "Nenhum documento pendente."
        configuracao["documentos"] = []
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

        # Processar tags customizadas para corretora
        if empresa.nicho == "corretora":
            lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
            if lead_seguro:
                # 1. Processar [ATUALIZAR_LEAD: campo=valor]
                tags_atualizacao = re.findall(r'\[ATUALIZAR_LEAD:\s*([^\]]+)\]', resposta_raw)
                for tag in tags_atualizacao:
                    try:
                        if '=' in tag:
                            campo, valor = tag.split('=', 1)
                            campo = campo.strip()
                            valor = valor.strip()
                            
                            if valor.lower() == 'true':
                                valor = True
                            elif valor.lower() == 'false':
                                valor = False
                            elif valor.lower() in ('null', 'none'):
                                valor = None
                            elif valor.isdigit():
                                valor = int(valor)
                            
                            if hasattr(lead_seguro, campo):
                                setattr(lead_seguro, campo, valor)
                                logger.info(f"[{telefone}] Campo LeadSeguro atualizado via tag: {campo} = {valor}")
                                if campo == "stage":
                                    lead.stage = valor
                                    lead_seguro.stage = valor
                                    db.commit()
                    except Exception as ex_tag:
                        logger.error(f"Erro ao processar tag de atualizacao '{tag}': {ex_tag}")
                
                # 2. Processar [SOLICITAR_HUMANO: motivo=...] ou transbordo
                if "[SOLICITAR_HUMANO" in resposta_raw:
                    motivo = "Solicitado pela IA"
                    match_h = re.search(r'\[SOLICITAR_HUMANO:\s*motivo=([^\]]+)\]', resposta_raw)
                    if match_h:
                        motivo = match_h.group(1).strip()
                    
                    atualizar_status_transbordo(db, empresa.id, telefone, "pausado", lead_id=lead.id)
                    logger.info(f"[{telefone}] Robô pausado devido à tag [SOLICITAR_HUMANO] (Motivo: {motivo}).")
                
                # 3. Processar [DOCUMENTO_RECEBIDO: tipo=...]
                tags_doc = re.findall(r'\[DOCUMENTO_RECEBIDO:\s*tipo=([^\]]+)\]', resposta_raw)
                for doc_tipo in tags_doc:
                    doc_tipo = doc_tipo.strip()
                    docs_r = lead_seguro.docs_recebidos or []
                    if doc_tipo not in [d.get("tipo") for d in docs_r]:
                        docs_r.append({"tipo": doc_tipo, "recebido_em": str(datetime.utcnow())})
                        lead_seguro.docs_recebidos = docs_r
                    
                    docs_p = lead_seguro.docs_pendentes or []
                    if doc_tipo in docs_p:
                        docs_p.remove(doc_tipo)
                        lead_seguro.docs_pendentes = docs_p
                    
                db.commit()

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

