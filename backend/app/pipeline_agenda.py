import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal, Lead, Mensagem, Empresa, Servico, Agendamento
from app.agents.especialistas import get_especialista
from app.parser_data import parse_data, parse_hora, obter_hoje_local, TZ_SP
from app.agenda_service import calcular_slots, criar_agendamento_cliente, confirmar_agendamento, recusar_agendamento, cancelar_agendamento, criar_agendamento

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
        whatsapp_prof = config_agenda.get("whatsapp_profissional") or config_agenda.get("whatsapp_professional")
        
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
                    "status": "ok",
                    "resposta": msg_resposta,
                    "tokens_in": 0,
                    "tokens_out": 0
                }

        # 2. GUARDRAIL: Modo de Recepção de Contatos (importado do pipeline central)
        from app.pipeline import _verificar_guardrails
        guardrails_resultado = _verificar_guardrails(db, empresa, telefone)
        if guardrails_resultado:
            if guardrails_resultado["status"] == "ignorado":
                return guardrails_resultado
            # status == "retomar": atendimento liberado, mas sem apresentação formal
        is_retomar = guardrails_resultado is not None and guardrails_resultado.get("status") == "retomar"

        # 3. CARREGAR OU CRIAR LEAD DO CLIENTE
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
        if not lead:
            lead = Lead(empresa_id=empresa.id, telefone=telefone, stage="novo")
            db.add(lead)
            db.commit()
            db.refresh(lead)

        dados_custom = lead.dados_customizados or {}
        if not isinstance(dados_custom, dict):
            dados_custom = {}
            
        agenda_estado = dados_custom.get("agenda_estado", "inicio")
        agenda_servico_id = dados_custom.get("agenda_servico_id", None)
        agenda_servico_nome = dados_custom.get("agenda_servico_nome", None)
        agenda_data = dados_custom.get("agenda_data", None)
        agenda_hora = dados_custom.get("agenda_hora", None)
        agenda_obs = dados_custom.get("agenda_obs", "")

        # Comando de reset para recomeçar o fluxo de agendamento do zero
        if mensagem_texto.strip().lower() in ["reset", "reiniciar", "recomeçar", "limpar"]:
            dados_custom["agenda_estado"] = "inicio"
            dados_custom["agenda_servico_id"] = None
            dados_custom["agenda_servico_nome"] = None
            dados_custom["agenda_data"] = None
            dados_custom["agenda_hora"] = None
            dados_custom["agenda_obs"] = ""
            dados_custom["agenda_caracteristica"] = None
            lead.dados_customizados = dados_custom
            flag_modified(lead, "dados_customizados")
            
            db.query(Mensagem).filter(Mensagem.lead_id == lead.id).delete()
            db.commit()
            
            return {
                "status": "ok",
                "resposta": "🔄 *Conversa reiniciada!* Como posso te ajudar hoje?",
                "tokens_in": 0,
                "tokens_out": 0
            }

        # Verifica se o lead está aguardando confirmação da lista de espera
        if agenda_estado == "aguardando_confirmacao_lista_espera":
            from app.database import ListaEspera
            lista_espera_id = dados_custom.get("lista_espera_id")
            lista_espera_item = db.query(ListaEspera).filter(ListaEspera.id == lista_espera_id).first() if lista_espera_id else None
            
            resp_limpa = mensagem_texto.strip().lower()
            if any(x in resp_limpa for x in ["sim", "quero", "confirmar", "aceito", "pode"]):
                if lista_espera_item and lista_espera_item.status == 'notificado':
                    hora_vaga = dados_custom.get("lista_espera_hora")
                    data_vaga = dados_custom.get("lista_espera_data")
                    serv_id = dados_custom.get("lista_espera_servico_id")
                    
                    ag = criar_agendamento(
                        db=db,
                        empresa_id=empresa.id,
                        lead_id=lead.id,
                        servico_id=serv_id,
                        data_str=data_vaga,
                        hora_inicio=hora_vaga,
                        observacao="Agendamento via lista de espera",
                        status="confirmado",
                        caracteristica=dados_custom.get("agenda_caracteristica")
                    )
                    
                    if ag:
                        lista_espera_item.status = 'confirmado'
                        db.commit()
                        
                        dados_custom["agenda_estado"] = "inicio"
                        dados_custom["agenda_servico_id"] = None
                        dados_custom["agenda_servico_nome"] = None
                        dados_custom["agenda_data"] = None
                        dados_custom["agenda_hora"] = None
                        dados_custom["agenda_obs"] = ""
                        dados_custom["agenda_caracteristica"] = None
                        lead.dados_customizados = dados_custom
                        flag_modified(lead, "dados_customizados")
                        db.commit()
                        
                        resposta_msg = f"Maravilhoso! Seu agendamento foi confirmado para o dia {datetime.strptime(data_vaga, '%Y-%m-%d').strftime('%d/%m/%Y')} às {hora_vaga}. Te esperamos lá!"
                        msg_assist = Mensagem(
                            empresa_id=empresa.id,
                            lead_id=lead.id,
                            tipo="assistente",
                            mensagem=resposta_msg,
                            timestamp=datetime.utcnow()
                        )
                        db.add(msg_assist)
                        db.commit()
                        
                        return {
                            "status": "ok",
                            "resposta": resposta_msg,
                            "tokens_in": 0,
                            "tokens_out": 0
                        }
                    else:
                        resposta_msg = "Desculpe, não conseguimos confirmar o agendamento. O slot pode ter sido preenchido."
                        dados_custom["agenda_estado"] = "inicio"
                        lead.dados_customizados = dados_custom
                        flag_modified(lead, "dados_customizados")
                        db.commit()
                        
                        return {
                            "status": "ok",
                            "resposta": resposta_msg,
                            "tokens_in": 0,
                            "tokens_out": 0
                        }
            elif any(x in resp_limpa for x in ["não", "nao", "recusar", "cancelar", "outro"]):
                if lista_espera_item:
                    lista_espera_item.status = 'recusado'
                    db.commit()
                    
                    from app.agenda_service import job_verificar_lista_espera
                    job_verificar_lista_espera(db, empresa.id, lista_espera_item.servico_id, lista_espera_item.data)
                
                dados_custom["agenda_estado"] = "inicio"
                lead.dados_customizados = dados_custom
                flag_modified(lead, "dados_customizados")
                db.commit()
                
                resposta_msg = "Tudo bem! Se precisar de outro horário ou serviço, basta mandar mensagem."
                msg_assist = Mensagem(
                    empresa_id=empresa.id,
                    lead_id=lead.id,
                    tipo="assistente",
                    mensagem=resposta_msg,
                    timestamp=datetime.utcnow()
                )
                db.add(msg_assist)
                db.commit()
                
                return {
                    "status": "ok",
                    "resposta": resposta_msg,
                    "tokens_in": 0,
                    "tokens_out": 0
                }

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
            slots = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data, dados_custom.get("agenda_caracteristica"))
            if slots:
                slots_formatados = ", ".join(slots)

        # 6. DETERMINISTIC PRE-PARSING DO INPUT DO CLIENTE
        if agenda_estado == "escolhendo_data":
            data_interpretada = parse_data(mensagem_texto)
            if data_interpretada:
                agenda_data = data_interpretada.strftime("%Y-%m-%d")
                agenda_estado = "escolhendo_hora"
                logger.info(f"[{telefone}] Data interpretada via Parser: {agenda_data}. Transição para escolhendo_hora.")
                
        elif agenda_estado == "escolhendo_hora":
            hora_interpretada = parse_hora(mensagem_texto)
            if hora_interpretada:
                if agenda_servico_id and agenda_data:
                    slots_livres = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data, dados_custom.get("agenda_caracteristica"))
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
            "obs": agenda_obs,
            "caracteristica": dados_custom.get("agenda_caracteristica") or ""
        }

        config_root = empresa.configuracoes.config if empresa.configuracoes else {}
        
        # Modo de Recepção: injeta flag para omitir apresentação formal para contatos conhecidos
        if is_retomar:
            config_root["_retomar_sem_apresentacao"] = True
        
        contexto_agente = {
            "config": config_root,
            "nome_agente": config_agenda.get("nome_agente") or config_root.get("nome_agente") or "Rosana",
            "nome_empresa": empresa.nome,
            "contexto_tempo": f"Data/Hora Atual: {datetime.now(TZ_SP).strftime('%d/%m/%Y %H:%M')}",
            "intencao": "agendamento",
            "stage": lead.stage,
            "servicos_formatados": servicos_formatados,
            "slots_formatados": slots_formatados,
            "dados_agenda": dados_agenda_ctx,
            "nicho": empresa.nicho or "agenda",
            "triagem_dinamica": {
                "campos_pendentes": "",
                "campos_coletados": ""
            }
        }

        # 9. PROCESSAR COM O ESPECIALISTA ADEQUADO
        nicho = empresa.nicho or "agenda"
        especialista = get_especialista(nicho)
        
        # Garante que um especialista focado em agenda seja usado se o nicho for genérico
        if especialista.nome not in ["EspecialistaAgenda", "EspecialistaBeleza"]:
            from app.agents.especialistas.agenda import EspecialistaAgenda
            especialista = EspecialistaAgenda()

        resposta_raw, t_in, t_out = especialista.processar(mensagem_texto, contexto_agente, historico)

        # 10. ATUALIZAR TOKENS CONSUMIDOS
        empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
        empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
        db.commit()

        logger.info(f"[{telefone}] Resposta crua {especialista.nome}: {resposta_raw}")

        # 11. PROCESSAR TAGS DA IA
        # A. [ESCOLHER_SERVICO: id=...]
        match_serv = re.search(r'\[ESCOLHER_SERVICO:\s*id=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_serv:
            serv_id_str = match_serv.group(1).strip()
            # Pode ser lista separada por vírgula para multi-serviços
            ids_split = [x.strip() for x in serv_id_str.split(",") if x.strip()]
            valid_ids = []
            nomes_servicos = []
            for s_id in ids_split:
                import uuid
                try:
                    uuid.UUID(s_id)
                    servico_obj = db.query(Servico).filter(Servico.id == s_id, Servico.empresa_id == empresa.id).first()
                    if servico_obj:
                        valid_ids.append(str(servico_obj.id))
                        nomes_servicos.append(servico_obj.nome)
                except ValueError:
                    pass
            
            if valid_ids:
                agenda_servico_id = ",".join(valid_ids)
                agenda_servico_nome = " + ".join(nomes_servicos)
                if agenda_estado == "inicio":
                    agenda_estado = "escolhendo_data"
                logger.info(f"[{telefone}] Tag escolheu serviço(s): {agenda_servico_nome}")
            else:
                logger.warning(f"[{telefone}] Tag [ESCOLHER_SERVICO] ignorada devido a IDs inválidos: '{serv_id_str}'")

        # B. [DEFINIR_CARACTERISTICA: caracteristica=...]
        match_caract = re.search(r'\[DEFINIR_CARACTERISTICA:\s*caracteristica=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_caract:
            caract_val = match_caract.group(1).strip()
            dados_custom["agenda_caracteristica"] = caract_val
            logger.info(f"[{telefone}] Tag característica: {caract_val}")

        # C. [ESCOLHER_DATA: data=...]
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

        # D. [ESCOLHER_HORA: hora=...]
        match_hora_tag = re.search(r'\[ESCOLHER_HORA:\s*hora=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_hora_tag:
            hora_val = match_hora_tag.group(1).strip()
            if agenda_servico_id and agenda_data:
                slots_livres = calcular_slots(db, empresa.id, agenda_servico_id, agenda_data, dados_custom.get("agenda_caracteristica"))
                if hora_val in slots_livres:
                    agenda_hora = hora_val
                    if agenda_estado == "escolhendo_hora":
                        agenda_estado = "coletando_obs"
                    logger.info(f"[{telefone}] Tag escolheu hora: {agenda_hora}")

        # E. [DEFINIR_OBS: obs=...]
        match_obs_tag = re.search(r'\[DEFINIR_OBS:\s*obs=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_obs_tag:
            obs_val = match_obs_tag.group(1).strip()
            agenda_obs = obs_val
            logger.info(f"[{telefone}] Tag obs: {agenda_obs}")

        # F. [SOLICITAR_AGENDAMENTO]
        if "[SOLICITAR_AGENDAMENTO]" in resposta_raw:
            if agenda_servico_id and agenda_data and agenda_hora:
                agendamento_db = criar_agendamento_cliente(
                    db=db,
                    empresa_id=empresa.id,
                    lead_id=lead.id,
                    servico_id=agenda_servico_id,
                    data_str=agenda_data,
                    hora_inicio=agenda_hora,
                    observacao=agenda_obs,
                    caracteristica=dados_custom.get("agenda_caracteristica")
                )
                
                if agendamento_db:
                    logger.info(f"[{telefone}] Agendamento #{agendamento_db.id} criado com sucesso.")
                    agenda_estado = "inicio"
                    agenda_servico_id = None
                    agenda_servico_nome = None
                    agenda_data = None
                    agenda_hora = None
                    agenda_obs = ""
                    dados_custom["agenda_caracteristica"] = None
                else:
                    resposta_raw = "Desculpe, o horário escolhido não está mais disponível. Por favor, selecione outro horário."
                    agenda_estado = "escolhendo_hora"
            else:
                logger.warning(f"[{telefone}] Tentativa de agendamento faltando dados. Servico={agenda_servico_id}, Data={agenda_data}, Hora={agenda_hora}")

        # G. [CONFIRMAR_RECORRENCIA: data=...]
        match_recor = re.search(r'\[CONFIRMAR_RECORRENCIA:\s*data=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_recor:
            data_futura = match_recor.group(1).strip()
            ultimo_ag = db.query(Agendamento).filter(
                Agendamento.lead_id == lead.id,
                Agendamento.empresa_id == empresa.id
            ).order_by(Agendamento.id.desc()).first()
            
            if ultimo_ag:
                criar_agendamento(
                    db=db,
                    empresa_id=empresa.id,
                    lead_id=lead.id,
                    servico_id=ultimo_ag.servico_id,
                    data_str=data_futura,
                    hora_inicio=ultimo_ag.hora_inicio,
                    observacao="Recorrência programada",
                    status="confirmado",
                    caracteristica=dados_custom.get("agenda_caracteristica")
                )
                logger.info(f"[{telefone}] Recorrência confirmada para {data_futura} às {ultimo_ag.hora_inicio}")

        # H. [LISTA_ESPERA]
        if "[LISTA_ESPERA]" in resposta_raw:
            if agenda_servico_id and agenda_data:
                from app.database import ListaEspera
                ja_espera = db.query(ListaEspera).filter(
                    ListaEspera.empresa_id == empresa.id,
                    ListaEspera.lead_id == lead.id,
                    ListaEspera.servico_id == agenda_servico_id,
                    ListaEspera.data == agenda_data,
                    ListaEspera.status == 'aguardando'
                ).first()
                
                if not ja_espera:
                    ultima_pos = db.query(ListaEspera).filter(
                        ListaEspera.empresa_id == empresa.id,
                        ListaEspera.servico_id == agenda_servico_id,
                        ListaEspera.data == agenda_data
                    ).count()
                    
                    novo_espera = ListaEspera(
                        empresa_id=empresa.id,
                        lead_id=lead.id,
                        servico_id=agenda_servico_id,
                        data=agenda_data,
                        status='aguardando',
                        posicao=ultima_pos + 1
                    )
                    db.add(novo_espera)
                    db.commit()
                    logger.info(f"[{telefone}] Adicionado à lista de espera na posição {ultima_pos + 1}")

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
        
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[ESCOLHER_SERVICO:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[ESCOLHER_DATA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[ESCOLHER_HORA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[DEFINIR_OBS:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[SOLICITAR_AGENDAMENTO\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[DEFINIR_CARACTERISTICA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[CONFIRMAR_RECORRENCIA:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[LISTA_ESPERA\]', '', resposta_limpa)
        
        resposta_limpa = re.sub(r'(?i)^\s*tags?\s*:\s*$', '', resposta_limpa, flags=re.MULTILINE)
        resposta_limpa = re.sub(r'\n{3,}', '\n\n', resposta_limpa)
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
            "status": "ok",
            "resposta": resposta_limpa,
            "tokens_in": t_in,
            "tokens_out": t_out
        }
    except Exception as e:
        logger.error(f"Erro no pipeline de agenda para {telefone}: {e}", exc_info=True)
        db.rollback()
        return {
            "status": "erro",
            "resposta": "Desculpe, ocorreu um erro ao processar o seu agendamento. Por favor, tente novamente mais tarde.",
            "tokens_in": 0,
            "tokens_out": 0
        }
    finally:
        db.close()
