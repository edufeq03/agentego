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

def _processar_modo_template(db, empresa, telefone, mensagem_texto):
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
        
        return {"status": "ok", "resposta": mensagem_inicial}
    except Exception as ex:
        logger.error(f"Erro ao processar template Piccolo: {ex}")
        return None

def _verificar_guardrails(db, empresa, telefone):
    configuracao = empresa.configuracoes.config if empresa.configuracoes else {}
    telefones_ignorados = configuracao.get('telefones_ignorados', [])
    
    # Normaliza o telefone recebido (remove caracteres não numéricos)
    tel_limpo = "".join(filter(str.isdigit, telefone))
    
    if tel_limpo in telefones_ignorados or telefone in telefones_ignorados:
        logger.info(f"Mensagem de {telefone} ignorada (Blacklist)")
        return {"status": "ignorado", "motivo": "blacklist"}
    return None

def _carregar_lead_com_billing(db, empresa, telefone):
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
    
    ultima_msg = db.query(Mensagem).filter(Mensagem.lead_id == lead.id if lead else False).order_by(Mensagem.timestamp.desc()).first()
    if not lead or not ultima_msg or ultima_msg.timestamp < (empresa.data_reset_contador - timedelta(days=31)):
        # Só incrementa se não for ilimitado ou se estiver abaixo do limite
        if empresa.plano != "ilimitado" and empresa.conversas_mes_atual >= empresa.limite_conversas_mes:
            return {
                "status": "limite_atingido", 
                "resposta": "Olá! No momento nosso atendimento automático atingiu o limite mensal. Por favor, aguarde que um atendente humano falará com você em breve. 🙏"
            }
        empresa.conversas_mes_atual = (empresa.conversas_mes_atual or 0) + 1
        db.commit()

    if not lead:
        from app.pipeline import carregar_lead
        lead = carregar_lead(db, empresa.id, telefone)
        
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
            
    return lead

def _atribuir_campanha_se_houver(db, empresa, lead, mensagem_texto):
    if not mensagem_texto:
        return
        
    # Regex para capturar [REF: CODIGO] ou [CAMPANHA: CODIGO]
    match = re.search(r"\[(?:REF|CAMPANHA):\s*([A-Za-z0-9_-]+)\]", mensagem_texto, re.IGNORECASE)
    if match:
        codigo_ref = match.group(1).upper().strip()
        logger.info(f"Tag de campanha detectada na mensagem: {codigo_ref}")
        
        # Buscar se a campanha existe no banco para esta empresa
        from app.database import Campanha
        campanha = db.query(Campanha).filter(
            Campanha.empresa_id == empresa.id,
            Campanha.codigo_ref == codigo_ref
        ).first()
        
        if campanha:
            # Atribuir campanha cadastrada
            lead.utm_campaign = campanha.codigo_ref
            lead.utm_source = campanha.origem
            lead.canal_entrada = campanha.origem
            db.commit()
            
            # Registrar evento de atribuição
            registrar_evento(db, empresa.id, lead.id, "campanha_atribuida", {
                "campanha_id": str(campanha.id),
                "codigo_ref": campanha.codigo_ref,
                "origem": campanha.origem
            })
            logger.info(f"Campanha '{campanha.nome}' atribuída ao lead {lead.id}")
        else:
            # Fallback se não existir pré-cadastro: salva o código textual
            lead.utm_campaign = codigo_ref
            lead.canal_entrada = "ads_generico"
            db.commit()
            logger.info(f"Tag de campanha '{codigo_ref}' vinculada como ad_generico (sem pré-cadastro)")

def _executar_triagem(db, empresa, mensagem_texto):
    from app.agents.triagem_agent import triagem_agent
    from app.classifier import classificar_intencao, analisar_sentimento_ia
    
    try:
        triagem = triagem_agent.analisar(mensagem_texto)
        logger.info(f"TriagemAgent executado com sucesso: intencao={triagem.get('intencao')}, sentimento={triagem.get('sentimento')}, urgente={triagem.get('urgente')}")
    except Exception as e:
        logger.warning(f"TriagemAgent falhou, usando fallback: {e}")
        intencao = classificar_intencao(mensagem_texto)
        sentimento, t_in, t_out = analisar_sentimento_ia(mensagem_texto)
        triagem = {
            "intencao": intencao,
            "sentimento": sentimento,
            "urgente": False,
            "resumo_curto": "mensagem não classificada",
            "tokens_in": t_in,
            "tokens_out": t_out
        }
        
    # Registra tokens consumidos
    t_in = triagem.get("tokens_in", 0)
    t_out = triagem.get("tokens_out", 0)
    empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
    empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
    db.commit()
    
    return triagem

def _salvar_mensagem_usuario(db, empresa, lead, mensagem_texto, triagem):
    msg_user = Mensagem(
        empresa_id=empresa.id, 
        lead_id=lead.id, 
        tipo="usuario", 
        mensagem=mensagem_texto, 
        intencao=triagem["intencao"]
    )
    db.add(msg_user)
    db.commit()
    
    sentimento = triagem["sentimento"]
    if sentimento == "negativo":
        registrar_evento(db, empresa.id, lead.id, "sentimento_negativo", {"mensagem": mensagem_texto})
    elif sentimento == "positivo":
        registrar_evento(db, empresa.id, lead.id, "sentimento_positivo")
        
    return msg_user

def _atualizar_stage(db, empresa, lead, intencao):
    etapas_empresa = empresa.etapas_funil or ["novo", "curioso", "interessado", "agendado"]
    novo_stage = calcular_stage(lead.stage, intencao, etapas_empresa)
    if novo_stage != lead.stage:
        lead.stage = novo_stage
        
        # Sincroniza LeadSeguro se aplicável
        if empresa.nicho == "corretora":
            lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
            if lead_seguro:
                lead_seguro.stage = novo_stage
                
        db.commit()
        
    # Registra evento de intenção
    registrar_evento(db, empresa.id, lead.id, f"perguntou_{intencao}" if intencao != "duvida" else "fez_pergunta")

def _montar_contexto(db, empresa, lead, triagem):
    configuracao = empresa.configuracoes.config if empresa.configuracoes else {}
    contexto_tempo = gerar_contexto_tempo(configuracao)
    
    # Injeta nicho e documentos no config para compatibilidade
    configuracao["nicho"] = empresa.nicho or "generico"
    documentos_legais = None
    
    if configuracao["nicho"] == "contabilidade":
        documentos_legais = db.query(DocumentoLegal).filter(
            DocumentoLegal.empresa_id == empresa.id, 
            DocumentoLegal.ativo == True
        ).all()
        configuracao["documentos"] = [{"titulo": d.titulo, "conteudo": d.conteudo} for d in documentos_legais]
    elif configuracao["nicho"] == "corretora":
        lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
        configuracao["dados_lead"] = formatar_dados_lead(lead_seguro)
        configuracao["docs_pendentes"] = ", ".join(lead_seguro.docs_pendentes) if (lead_seguro and lead_seguro.docs_pendentes) else "Nenhum documento pendente."
        configuracao["documentos"] = []
    else:
        configuracao["documentos"] = []
        
    return {
        "configuracao": configuracao,
        "contexto_tempo": contexto_tempo,
        "documentos_legais": documentos_legais
    }

def _gerar_resposta(db, empresa, lead, mensagem_texto, ctx, status_transbordo, historico):
    if status_transbordo == "aguardando":
        return processar_confirmacao_transbordo(mensagem_texto, historico=historico)
    else:
        configuracao = ctx["configuracao"]
        contexto_tempo = ctx["contexto_tempo"]
        intencao = ctx["intencao"]
        sentimento = ctx["sentimento"]
        documentos_legais = ctx.get("documentos_legais")
        
        lead_seguro = None
        if empresa.nicho == "corretora":
            lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
            
        return processar_mensagem_dinamica(
            mensagem_texto, 
            configuracao, 
            intencao, 
            lead.stage, 
            contexto_tempo, 
            historico=historico, 
            sentimento=sentimento,
            empresa=empresa,
            lead=lead,
            lead_seguro=lead_seguro,
            documentos_legais=documentos_legais
        )

def _processar_tags(db, empresa, lead, resposta_raw, telefone):
    # Processar transbordo / suspensão baseada em tags
    if "[CONFIRMAR_TRANSBORDO]" in resposta_raw:
        atualizar_status_transbordo(db, empresa.id, telefone, "pausado", lead_id=lead.id)
    elif "[CANCELAR_TRANSBORDO]" in resposta_raw:
        atualizar_status_transbordo(db, empresa.id, telefone, None, lead_id=lead.id)
    elif "[SUGERIR_TRANSBORDO]" in resposta_raw:
        atualizar_status_transbordo(db, empresa.id, telefone, "aguardando", lead_id=lead.id)

    # === PROCESSAMENTO GLOBAL DE TAGS DE TRIAGEM DINÂMICA (SaaS Global) ===
    
    # 1. Carregar/Inicializar dados customizados do lead
    dados_customizados = lead.dados_customizados or {}
    if not isinstance(dados_customizados, dict):
        dados_customizados = {}
        
    lead_atualizado = False
    
    # 2. Encontrar todas as tags [ATUALIZAR_LEAD: campo=valor]
    tags_atualizacao = re.findall(r'\[ATUALIZAR_LEAD:\s*([^\]]+)\]', resposta_raw)
    
    # Compatibilidade legado com corretora
    lead_seguro = None
    if empresa.nicho == "corretora":
        lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
        
    for tag_content in tags_atualizacao:
        parts = tag_content.split(',')
        for part in parts:
            try:
                if '=' in part:
                    campo, valor = part.split('=', 1)
                    campo = campo.strip().lower().replace(" ", "_")
                    valor = valor.strip()
                    
                    if not campo:
                        continue
                        
                    # Converter tipo primitivo se necessário
                    if valor.lower() in ('true', 'sim'):
                        valor = True
                    elif valor.lower() in ('false', 'nao', 'não'):
                        valor = False
                    elif valor.lower() in ('null', 'none'):
                        valor = None
                    elif valor.isdigit():
                        valor = int(valor)
                    
                    # Salvar no dicionário dinâmico global
                    dados_customizados[campo] = valor
                    lead_atualizado = True
                    logger.info(f"[{telefone}] Campo dinâmico atualizado via tag: {campo} = {valor}")
                    
                    # Sincronização retrativa com colunas físicas de LeadSeguro (para corretoras)
                    if lead_seguro:
                        # Se for um campo de data/idade especial, aplica parser resiliente
                        if campo in ('idade_segurado', 'idade_condutor') and not isinstance(valor, bool) and valor is not None:
                            val_str = str(valor)
                            match_date = re.search(r'(\d{2})[/-](\d{2})[/-](\d{4})', val_str)
                            if match_date:
                                dia, mes, ano = map(int, match_date.groups())
                                from datetime import date
                                hoje = date.today()
                                valor_parsed = hoje.year - ano - ((hoje.month, hoje.day) < (mes, dia))
                            else:
                                match_year = re.search(r'\b(19\d{2}|20\d{2})\b', val_str)
                                if match_year:
                                    ano = int(match_year.group(1))
                                    from datetime import date
                                    valor_parsed = date.today().year - ano
                                else:
                                    valor_parsed = valor
                        else:
                            valor_parsed = valor
                            
                        if hasattr(lead_seguro, campo):
                            setattr(lead_seguro, campo, valor_parsed)
                            logger.info(f"[{telefone}] Legacy LeadSeguro sincronizado retrativamente: {campo} = {valor_parsed}")
                            if campo == "stage":
                                lead.stage = valor_parsed
                                lead_seguro.stage = valor_parsed
            except Exception as ex_tag:
                logger.error(f"Erro ao processar parte da tag de atualizacao '{part}': {ex_tag}")
                
    if lead_atualizado:
        from sqlalchemy.orm.attributes import flag_modified
        lead.dados_customizados = dados_customizados
        flag_modified(lead, "dados_customizados")
        db.commit()

    # 3. Processar [SOLICITAR_HUMANO: motivo=...] ou transbordo global
    if "[SOLICITAR_HUMANO" in resposta_raw:
        motivo = "Triagem concluída - pronto para atendimento"
        match_h = re.search(r'\[SOLICITAR_HUMANO:\s*motivo=([^\]]+)\]', resposta_raw)
        if match_h:
            motivo = match_h.group(1).strip()
        
        atualizar_status_transbordo(db, empresa.id, telefone, "pausado", lead_id=lead.id)
        logger.info(f"[{telefone}] Robô pausado devido à tag global [SOLICITAR_HUMANO] (Motivo: {motivo}).")
        
        # Notificar dono/corretor se for nicho de corretora
        if empresa.nicho == "corretora" and lead_seguro:
            config = empresa.configuracoes.config if empresa.configuracoes else {}
            tel_corretor = config.get("telefone_notificacao") or config.get("telefone_corretor") or empresa.telefone_proprietario
            if tel_corretor:
                tel_corretor_limpo = "".join(filter(str.isdigit, str(tel_corretor)))
                if tel_corretor_limpo:
                    if len(tel_corretor_limpo) in (10, 11):
                        tel_corretor_limpo = "55" + tel_corretor_limpo
                        
                    dados_lead_formatado = formatar_dados_lead(lead_seguro)
                    tipo_seguro_str = (lead_seguro.tipo_seguro or "não informado").upper()
                    
                    mensagem_alerta = (
                        f"🚨 *NOVO LEAD DE SEGURO CADASTRADO* 🚨\n\n"
                        f"Olá! O assistente virtual concluiu a triagem de um novo lead:\n\n"
                        f"👤 *Nome:* {lead.nome or lead_seguro.nome_segurado or 'Não informado'}\n"
                        f"📱 *WhatsApp do Lead:* https://wa.me/{telefone}\n"
                        f"📋 *Interesse:* {tipo_seguro_str}\n\n"
                        f"📊 *Dados Coletados:*\n"
                        f"{dados_lead_formatado}\n\n"
                        f"⚡ *Status:* {motivo}\n\n"
                        f"_O robô foi pausado automaticamente. Você já pode assumir o atendimento!_"
                    )
                    
                    try:
                        enviar_whatsapp(tel_corretor_limpo, mensagem_alerta, empresa.evolution_instance)
                        logger.info(f"[{telefone}] Notificação de transbordo enviada para {tel_corretor_limpo}")
                    except Exception as ex_notif:
                        logger.error(f"Erro ao enviar notificação no WhatsApp: {ex_notif}")
        db.commit()

    # 4. Processar [DOCUMENTO_RECEBIDO: tipo=...] para corretora
    if empresa.nicho == "corretora" and lead_seguro:
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

def _finalizar(db, empresa, lead, resposta_raw, resposta_limpa, t_in, t_out):
    # Registra tokens da resposta principal
    empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
    empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
    
    # Para o nicho de corretora, mantemos as tags na mensagem salva no banco para evitar que o modelo imite histórico limpo
    msg_mensagem = resposta_raw if empresa.nicho == "corretora" else resposta_limpa
    
    msg_bot = Mensagem(empresa_id=empresa.id, lead_id=lead.id, tipo="agente", mensagem=msg_mensagem)
    db.add(msg_bot)
    db.commit()

def processar_webhook(empresa: Empresa, telefone: str, mensagem_texto: str):
    db = SessionLocal()
    try:
        # ETAPA 0: Template externo (Piccolo Seguros)
        if empresa.nicho == "corretora" and detectar_template_seguro(mensagem_texto):
            res = _processar_modo_template(db, empresa, telefone, mensagem_texto)
            if res:
                return res

        # ETAPA 1: Guardrails (blacklist, limite de plano)
        guardrails = _verificar_guardrails(db, empresa, telefone)
        if guardrails:
            return guardrails

        # ETAPA 2: Transbordo ativo?
        status_transbordo = obter_status_transbordo(db, empresa.id, telefone)
        if status_transbordo == "pausado":
            return {"status": "pausado", "motivo": "transbordo_ativo"}

        # ETAPA 3: Carregar/criar lead com controle de billing
        lead_or_billing = _carregar_lead_com_billing(db, empresa, telefone)
        if isinstance(lead_or_billing, dict):
            # Limite atingido
            return lead_or_billing
        lead = lead_or_billing
        
        # Atribuir campanha se houver tags de marketing na mensagem
        _atribuir_campanha_se_houver(db, empresa, lead, mensagem_texto)

        # ETAPA 4: Triagem (IA — intenção + sentimento)
        triagem = _executar_triagem(db, empresa, mensagem_texto)

        # ETAPA 5: Salvar mensagem do usuário
        msg_user = _salvar_mensagem_usuario(db, empresa, lead, mensagem_texto, triagem)

        # ETAPA 6: Atualizar stage do funil
        _atualizar_stage(db, empresa, lead, triagem["intencao"])

        # ETAPA 7: Montar contexto
        context_data = _montar_contexto(db, empresa, lead, triagem)

        # ETAPA 8: Carregar histórico recente (limitado a 6)
        historico_db = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).limit(6).all()
        historico = []
        for m in reversed(historico_db):
            role = "user" if m.tipo == "usuario" else "assistant"
            # Não adicionamos a mensagem que acabamos de receber
            if m.id != msg_user.id:
                historico.append({"role": role, "content": m.mensagem})

        # ETAPA 9: Gerar resposta
        ctx_para_gerar = {
            "configuracao": context_data["configuracao"],
            "contexto_tempo": context_data["contexto_tempo"],
            "intencao": triagem["intencao"],
            "sentimento": triagem["sentimento"],
            "documentos_legais": context_data["documentos_legais"]
        }
        
        resposta_raw, t_in, t_out = _gerar_resposta(
            db, empresa, lead, mensagem_texto, ctx_para_gerar, status_transbordo, historico
        )

        # ETAPA 10: Processar tags da resposta
        _processar_tags(db, empresa, lead, resposta_raw, telefone)

        # ETAPA 11: Limpar tags e salvar tokens/mensagem do agente
        resposta_limpa = limpar_tags(resposta_raw)
        _finalizar(db, empresa, lead, resposta_raw, resposta_limpa, t_in, t_out)

        logger.info(f"Resposta gerada para {telefone}", extra={"empresa_id": str(empresa.id), "lead_id": str(lead.id), "tipo": "ia_response"})

        return {"status": "ok", "resposta": resposta_limpa}

    except Exception as ex:
        logger.error(f"Erro fatal no processar_webhook: {ex}", exc_info=True)
        return {"status": "erro", "motivo": str(ex)}
    finally:
        db.close()
