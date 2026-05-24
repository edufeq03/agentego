import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal, Lead, Mensagem, Empresa, Servico, Agendamento
from app.agents.especialistas import get_especialista
from app.parser_data import parse_data, parse_hora, obter_hoje_local
from app.agenda_service import calcular_slots, criar_agendamento_cliente, confirmar_agendamento, recusar_agendamento, cancelar_agendamento

logger = logging.getLogger(__name__)

def formatar_servicos_para_ia(servicos: list) -> str:
    if not servicos:
        return "Nenhum serviço cadastrado ou disponível no momento."
    linhas = []
    for s in servicos:
        preco_str = f"R$ {s.preco:.2f}" if s.preco is not None else "Gratuito"
        linhas.append(f"• *{s.nome}* - {s.duracao_min} min ({preco_str}) [ID: {s.id}]")
    return "\n".join(linhas)

def processar_pipeline_agenda(empresa: Empresa, telefone: str, mensagem_texto: str) -> dict:
    """
    Pipeline de conversação para o Módulo de Agenda.
    Lida com a máquina de estados de agendamento (inicio -> escolhendo_servico -> escolhendo_data -> escolhendo_hora -> coletando_obs -> solicitado).
    Também processa comandos do profissional (ex: '7 confirmar', '7 recusar Horário cheio').
    """
    db = SessionLocal()
    try:
        config_agenda = empresa.configuracoes.config.get("agenda", {}) if empresa.configuracoes else {}
        whatsapp_prof = config_agenda.get("whatsapp_professional")
        
        # 1. PROCESSAR COMANDOS DO PROFISSIONAL
        # Comandos: "<id> confirmar" ou "<id> recusar [motivo]"
        # Remove caracteres especiais do telefone para comparação
        tel_limpo = telefone.replace(" ", "").replace("-", "").replace("+", "")
        prof_limpo = str(whatsapp_prof).replace(" ", "").replace("-", "").replace("+", "") if whatsapp_prof else ""
        
        is_prof = False
        if prof_limpo and (tel_limpo == prof_limpo or tel_limpo.endswith(prof_limpo) or prof_limpo.endswith(tel_limpo)):
            is_prof = True
            
        if is_prof:
            match_cmd = re.match(r'^\s*(\d+)\s+(confirmar|recusar|cancelar)(?:\s+(.*))?$', mensagem_texto, re.IGNORECASE)
            if match_cmd:
                agendamento_id = int(match_cmd.group(1))
                acao = match_cmd.group(2).lower()
                motivo = match_cmd.group(3) or ""
                
                logger.info(f"[Profissional {telefone}] Comando recebido: ID={agendamento_id}, Ação={acao}, Motivo={motivo}")
                
                sucesso = False
                msg_resposta = ""
                if acao == "confirmar":
                    sucesso = confirmar_agendamento(db, agendamento_id)
                    msg_resposta = f"✅ Agendamento #{agendamento_id} *confirmado* com sucesso!" if sucesso else f"❌ Não foi possível confirmar o agendamento #{agendamento_id}."
                elif acao == "recusar":
                    sucesso = recusar_agendamento(db, agendamento_id, motivo)
                    msg_resposta = f"❌ Agendamento #{agendamento_id} *recusado*!" if sucesso else f"❌ Não foi possível recusar o agendamento #{agendamento_id}."
                elif acao == "cancelar":
                    sucesso = cancelar_agendamento(db, agendamento_id, motivo)
                    msg_resposta = f"⚠️ Agendamento #{agendamento_id} *cancelado*!" if sucesso else f"❌ Não foi possível cancelar o agendamento #{agendamento_id}."
                
                return {
                    "resposta": msg_resposta,
                    "tokens_in": 0,
                    "tokens_out": 0
                }

        # 2. CARREGAR OU CRIAR LEAD DO CLIENTE
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
        if not lead:
            lead = Lead(empresa_id=empresa.id, telefone=telefone, stage="novo")
            db.add(lead)
            db.commit()
            db.refresh(lead)

        # Inicializa dados customizados se necessário
        dados_custom = lead.dados_customizados or {}
        if not isinstance(dados_custom, dict):
            dados_custom = {}
            
        agenda_estado = dados_custom.get("agenda_estado", "inicio")
        agenda_servico_id = dados_custom.get("agenda_servico_id", None)
        agenda_servico_nome = dados_custom.get("agenda_servico_nome", None)
        agenda_data = dados_custom.get("agenda_data", None)
        agenda_hora = dados_custom.get("agenda_hora", None)
        agenda_obs = dados_custom.get("agenda_obs", "")

        # 3. REGISTRAR MENSAGEM DO USUÁRIO
        msg_usuario = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead.id,
            tipo="usuario",
            mensagem=mensagem_texto,
            timestamp=datetime.utcnow()
        )
        db.add(msg_usuario)
        db.commit()

        # 4. CARREGAR SERVICOS
        servicos = db.query(Servico).filter(Servico.empresa_id == empresa.id, Servico.ativo == True).all()
        servicos_formatados = formatar_servicos_para_ia(servicos)

        # 5. PREPARAR SLOTS E DATAS SE HOUVER SERVIÇO E DATA SELECIONADOS
        slots_formatados = "Nenhum horário disponível para esta data."
        if agenda_servico_id and agenda_data:
            slots = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data)
            if slots:
                slots_formatados = ", ".join(slots)

        # 6. DETERMINISTIC PRE-PARSING DO INPUT DO CLIENTE (Facilita muito para a IA)
        # Tenta interpretar data e hora diretamente do input do usuário para acelerar transições
        if agenda_estado == "escolhendo_data":
            data_interpretada = parse_data(mensagem_texto)
            if data_interpretada:
                agenda_data = data_interpretada.strftime("%Y-%m-%d")
                agenda_estado = "escolhendo_hora"
                logger.info(f"[{telefone}] Data interpretada via Parser: {agenda_data}. Transição para escolhendo_hora.")
                
        elif agenda_estado == "escolhendo_hora":
            hora_interpretada = parse_hora(mensagem_texto)
            if hora_interpretada:
                # Se temos data e serviço, validamos se a hora é válida
                if agenda_servico_id and agenda_data:
                    slots_livres = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data)
                    if hora_interpretada in slots_livres:
                        agenda_hora = hora_interpretada
                        agenda_estado = "coletando_obs"
                        logger.info(f"[{telefone}] Hora interpretada via Parser: {agenda_hora}. Transição para coletando_obs.")

        # 7. HISTÓRICO DE MENSAGENS PARA A IA (últimas 6)
        historico_db = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).limit(6).all()
        historico = []
        for m in reversed(historico_db):
            if m.id != msg_usuario.id:
                role = "user" if m.tipo == "usuario" else "assistant"
                historico.append({"role": role, "content": m.mensagem})

        # 8. CONTEXTO PARA O AGENTE
        dados_agenda_ctx = {
            "estado": agenda_estado,
            "servico_id": agenda_servico_id,
            "servico_nome": agenda_servico_nome or "Não definido",
            "data": agenda_data or "Não definida",
            "hora": agenda_hora or "Não definida",
            "obs": agenda_obs
        }

        contexto_agente = {
            "config": empresa.configuracoes.config if empresa.configuracoes else {},
            "nome_agente": config_agenda.get("nome_agente", "Rosana"),
            "nome_empresa": empresa.nome,
            "contexto_tempo": f"Data/Hora Atual: {datetime.now(TZ_SP).strftime('%d/%m/%Y %H:%M')}",
            "intencao": "agendamento",
            "stage": lead.stage,
            "servicos_formatados": servicos_formatados,
            "slots_formatados": slots_formatados,
            "dados_agenda": dados_agenda_ctx
        }

        # 9. PROCESSAR COM O ESPECIALISTA DE AGENDA
        especialista = get_especialista("agenda")
        resposta_raw, t_in, t_out = especialista.processar(mensagem_texto, contexto_agente, historico)

        # 10. ATUALIZAR TOKENS CONSUMIDOS
        empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
        empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
        db.commit()

        logger.info(f"[{telefone}] Resposta crua EspecialistaAgenda: {resposta_raw}")

        # 11. PROCESSAR TAGS DA IA
        # A. [ESCOLHER_SERVICO: id=...]
        match_serv = re.search(r'\[ESCOLHER_SERVICO:\s*id=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_serv:
            serv_id_str = match_serv.group(1).strip()
            servico_obj = db.query(Servico).filter(Servico.id == serv_id_str, Servico.empresa_id == empresa.id).first()
            if servico_obj:
                agenda_servico_id = str(servico_obj.id)
                agenda_servico_nome = servico_obj.nome
                if agenda_estado == "inicio":
                    agenda_estado = "escolhendo_data"
                logger.info(f"[{telefone}] Tag escolheu serviço: {agenda_servico_nome}")

        # B. [ESCOLHER_DATA: data=...]
        match_data_tag = re.search(r'\[ESCOLHER_DATA:\s*data=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_data_tag:
            data_val = match_data_tag.group(1).strip()
            try:
                datetime.strptime(data_val, "%Y-%m-%d")
                agenda_data = data_val
                if agenda_estado == "escolhendo_data":
                    agenda_estado = "escolhendo_hora"
                logger.info(f"[{telefone}] Tag escolheu data: {agenda_data}")
            except ValueError:
                pass

        # C. [ESCOLHER_HORA: hora=...]
        match_hora_tag = re.search(r'\[ESCOLHER_HORA:\s*hora=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_hora_tag:
            hora_val = match_hora_tag.group(1).strip()
            # Valida
            if agenda_servico_id and agenda_data:
                slots_livres = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data)
                if hora_val in slots_livres:
                    agenda_hora = hora_val
                    if agenda_estado == "escolhendo_hora":
                        agenda_estado = "coletando_obs"
                    logger.info(f"[{telefone}] Tag escolheu hora: {agenda_hora}")

        # D. [DEFINIR_OBS: obs=...]
        match_obs_tag = re.search(r'\[DEFINIR_OBS:\s*obs=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_obs_tag:
            obs_val = match_obs_tag.group(1).strip()
            agenda_obs = obs_val
            logger.info(f"[{telefone}] Tag obs: {agenda_obs}")

        # E. [SOLICITAR_AGENDAMENTO]
        if "[SOLICITAR_AGENDAMENTO]" in resposta_raw:
            if agenda_servico_id and agenda_data and agenda_hora:
                # Criar o agendamento pendente no banco e enviar para aprovação
                agendamento_db = criar_agendamento_cliente(
                    db=db,
                    empresa_id=empresa.id,
                    lead_id=lead.id,
                    servico_id=agenda_servico_id,
                    data_str=agenda_data,
                    hora_inicio=agenda_hora,
                    observacao=agenda_obs
                )
                
                if agendamento_db:
                    logger.info(f"[{telefone}] Agendamento #{agendamento_db.id} criado com sucesso.")
                    # Limpa carrinho de agendamento do lead
                    agenda_estado = "inicio"
                    agenda_servico_id = None
                    agenda_servico_nome = None
                    agenda_data = None
                    agenda_hora = None
                    agenda_obs = ""
                else:
                    resposta_raw = "Desculpe, o horário escolhido não está mais disponível. Por favor, selecione outro horário."
                    agenda_estado = "escolhendo_hora"
            else:
                logger.warning(f"[{telefone}] Tentativa de agendamento faltando dados. Servico={agenda_servico_id}, Data={agenda_data}, Hora={agenda_hora}")

        # 12. SALVAR ESTADOS NO LEAD
        dados_custom["agenda_estado"] = agenda_estado
        dados_custom["agenda_servico_id"] = agenda_servico_id
        dados_custom["agenda_servico_nome"] = agenda_servico_nome
        dados_custom["agenda_data"] = agenda_data
        dados_custom["agenda_hora"] = agenda_hora
        dados_custom["agenda_obs"] = agenda_obs
        
        lead.dados_customizados = dados_custom
        flag_modified(lead, "dados_customizados")
        db.commit()

        # 13. LIMPAR TAGS DA RESPOSTA PARA O CLIENTE
        resposta_limpa = resposta_raw
        resposta_limpa = re.sub(r'\[ESCOLHER_SERVICO:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[ESCOLHER_DATA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[ESCOLHER_HORA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[DEFINIR_OBS:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[SOLICITAR_AGENDAMENTO\]', '', resposta_limpa)
        resposta_limpa = resposta_limpa.strip()

        # Registrar resposta da assistente no banco
        msg_assistente = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead.id,
            tipo="assistente",
            mensagem=resposta_limpa,
            timestamp=datetime.utcnow()
        )
        db.add(msg_assistente)
        db.commit()

        return {
            "resposta": resposta_limpa,
            "tokens_in": t_in,
            "tokens_out": t_out
        }
    except Exception as e:
        logger.error(f"Erro no pipeline de agenda para {telefone}: {e}")
        db.rollback()
        return {
            "resposta": "Desculpe, ocorreu um erro ao processar o seu agendamento. Por favor, tente novamente mais tarde.",
            "tokens_in": 0,
            "tokens_out": 0
        }
    finally:
        db.close()
