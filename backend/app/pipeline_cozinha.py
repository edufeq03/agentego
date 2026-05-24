import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, Pedido, Cardapio, Empresa, Lead
from app.pedido_service import atualizar_status_pedido, obter_pedido_por_numero, obter_pedidos_ativos
from app.cardapio_service import listar_itens, obter_item_por_nome
from app.whatsapp import enviar_whatsapp

from app.estado_auxiliar import carregar_estado_auxiliar, salvar_estado_auxiliar, limpar_estado_auxiliar
from app.extrator_agenda import (
    extrair_dados_agendamento,
    validar_extracao,
    resolver_cliente,
    calcular_hora_fim,
    montar_resumo_agendamento,
    montar_mensagem_confirmacao_cliente,
    buscar_lead_por_nome,
    buscar_servico_por_nome
)
from app.agenda_service import criar_agendamento, buscar_agendamento_por_cliente_data, cancelar_agendamento

logger = logging.getLogger(__name__)

PALAVRAS_GATILHO_AGENDA = [
    "agenda", "agendar", "marcar", "marca", "reservar",
    "faxina", "limpeza", "higienização", "consulta", "sessão",
    "cancelar agendamento", "remarcar", "reagendar", "cancelar",
    "detalhes", "quando é", "compromisso"
]

def tem_intencao_agenda(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(p in texto_lower for p in PALAVRAS_GATILHO_AGENDA)

async def prosseguir_fluxo_agenda(db: Session, empresa: Empresa, dados: dict, faltando: list, telefone_auxiliar: str) -> dict:
    config = empresa.configuracoes.config if empresa.configuracoes else {}
    
    # 1. Tratar data no passado
    if "data_passada" in faltando:
        salvar_estado_auxiliar(db, empresa.id, {
            "aguardando": "campo_agenda",
            "campo": "data",
            "dados_parciais": dados
        })
        return {"status": "ok", "resposta": "⚠️ Essa data já passou. Qual a data correta para o agendamento?"}

    # 2. Tratar hora indisponível
    if "hora_indisponivel" in faltando:
        from app.agenda_service import calcular_slots
        slots = calcular_slots(db, empresa.id, dados["servico_id"], dados["data"])
        slots_txt = " | ".join(slots) if slots else "nenhum disponível"
        salvar_estado_auxiliar(db, empresa.id, {
            "aguardando": "campo_agenda",
            "campo": "hora",
            "dados_parciais": dados
        })
        return {
            "status": "ok",
            "resposta": f"⚠️ O horário {dados['hora']} não está disponível no dia {datetime.strptime(dados['data'], '%Y-%m-%d').strftime('%d/%m/%Y')}.\n\n"
                        f"Horários livres: {slots_txt}\n\nQual horário você prefere?"
        }

    # 3. Tratar campos comuns faltando
    if faltando:
        campo = faltando[0]
        if campo == "servico":
            from app.extrator_agenda import carregar_servicos
            servs = carregar_servicos(db, empresa.id)
            servs_txt = ", ".join([s["nome"] for s in servs])
            pergunta = f"Qual o serviço? Opções disponíveis: {servs_txt}"
        elif campo == "data":
            pergunta = "Qual a data do agendamento?"
        elif campo == "hora":
            from app.agenda_service import calcular_slots
            slots = calcular_slots(db, empresa.id, dados["servico_id"], dados["data"])
            slots_txt = " | ".join(slots) if slots else "nenhum"
            pergunta = f"Qual o horário? Slots livres: {slots_txt}"
        else:
            pergunta = f"Qual o {campo}?"
            
        salvar_estado_auxiliar(db, empresa.id, {
            "aguardando": "campo_agenda",
            "campo": campo,
            "dados_parciais": dados
        })
        return {"status": "ok", "resposta": pergunta}

    # 4. Resolver cliente
    lead_res = await resolver_cliente(db, empresa.id, dados, telefone_auxiliar, config)
    if lead_res == "aguardando_telefone":
        return {"status": "ok", "resposta": "Aguardando informações do cliente..."}
        
    dados["lead_id"] = lead_res
    
    # 5. Tudo OK -> Exibir resumo e pedir confirmação
    hora_fim = calcular_hora_fim(dados["hora"], dados["servico_duracao"])
    resumo = montar_resumo_agendamento(dados, hora_fim)
    
    salvar_estado_auxiliar(db, empresa.id, {
        "aguardando": "confirmacao_agenda",
        "dados_parciais": dados
    })
    
    return {
        "status": "ok",
        "resposta": f"Vou criar este agendamento:\n\n{resumo}\n\nConfirma? (sim/não)"
    }

def processar_comando_cancelamento(db: Session, empresa: Empresa, dados: dict) -> dict:
    from app.database import Agendamento
    ag = None
    if dados.get("numero_agendamento"):
        try:
            ag_id = int(re.sub(r"\D", "", str(dados["numero_agendamento"])))
            ag = db.query(Agendamento).filter(Agendamento.id == ag_id, Agendamento.empresa_id == empresa.id).first()
        except ValueError:
            pass
    
    if not ag and dados.get("cliente_nome"):
        leads = buscar_lead_por_nome(db, empresa.id, dados["cliente_nome"])
        if len(leads) == 1:
            lead = leads[0]
            if dados.get("data"):
                ag = db.query(Agendamento).filter(
                    Agendamento.empresa_id == empresa.id,
                    Agendamento.lead_id == lead.id,
                    Agendamento.data == dados["data"],
                    Agendamento.status.in_(['confirmado', 'pendente'])
                ).first()
            else:
                ag = db.query(Agendamento).filter(
                    Agendamento.empresa_id == empresa.id,
                    Agendamento.lead_id == lead.id,
                    Agendamento.status.in_(['confirmado', 'pendente'])
                ).order_by(Agendamento.criado_em.desc()).first()
                
    if ag:
        sucesso = cancelar_agendamento(db, ag.id, "Cancelado via WhatsApp pelo profissional")
        if sucesso:
            return {"status": "ok", "resposta": f"❌ Agendamento #{ag.id} cancelado com sucesso e cliente notificado!"}
        else:
            return {"status": "ok", "resposta": f"⚠️ Não foi possível cancelar o agendamento #{ag.id}."}
    else:
        return {"status": "ok", "resposta": "⚠️ Não encontrei nenhum agendamento pendente ou confirmado correspondente para cancelar."}

def processar_comando_reagendamento(db: Session, empresa: Empresa, dados: dict) -> dict:
    from app.database import Agendamento
    ag = None
    if dados.get("numero_agendamento"):
        try:
            ag_id = int(re.sub(r"\D", "", str(dados["numero_agendamento"])))
            ag = db.query(Agendamento).filter(Agendamento.id == ag_id, Agendamento.empresa_id == empresa.id).first()
        except ValueError:
            pass
            
    if not ag and dados.get("cliente_nome"):
        leads = buscar_lead_por_nome(db, empresa.id, dados["cliente_nome"])
        if len(leads) == 1:
            lead = leads[0]
            ag = db.query(Agendamento).filter(
                Agendamento.empresa_id == empresa.id,
                Agendamento.lead_id == lead.id,
                Agendamento.status.in_(['confirmado', 'pendente'])
            ).order_by(Agendamento.criado_em.desc()).first()
            
    if not ag:
        return {"status": "ok", "resposta": "⚠️ Não encontrei o agendamento original para reagendar."}
        
    nova_data = dados.get("data") or ag.data
    nova_hora = dados.get("hora") or ag.hora_inicio
    
    from app.agenda_service import calcular_slots
    slots = calcular_slots(db, empresa.id, ag.servico_id, nova_data)
    
    # Se o slot original do agendamento for o mesmo e a data a mesma, permitimos!
    if nova_hora not in slots and not (nova_data == ag.data and nova_hora == ag.hora_inicio):
        slots_txt = " | ".join(slots) if slots else "nenhum"
        return {
            "status": "ok",
            "resposta": f"⚠️ O horário {nova_hora} não está disponível no dia {datetime.strptime(nova_data, '%Y-%m-%d').strftime('%d/%m/%Y')}.\n\n"
                        f"Slots disponíveis: {slots_txt}"
        }
        
    salvar_estado_auxiliar(db, empresa.id, {
        "aguardando": "confirmacao_edicao",
        "agendamento_id": ag.id,
        "nova_data": nova_data,
        "nova_hora": nova_hora
    })
    
    data_de = datetime.strptime(ag.data, "%Y-%m-%d").strftime("%d/%m")
    data_para = datetime.strptime(nova_data, "%Y-%m-%d").strftime("%d/%m")
    
    return {
        "status": "ok",
        "resposta": f"Deseja reagendar o compromisso #{ag.id}?\n\n"
                    f"🔄 *DE:* {data_de} às {ag.hora_inicio}\n"
                    f"➡️ *PARA:* {data_para} às {nova_hora}\n\n"
                    f"Confirma? (sim/não)"
    }

def processar_comando_detalhes(db: Session, empresa: Empresa, dados: dict) -> dict:
    from app.database import Agendamento
    ag = None
    if dados.get("numero_agendamento"):
        try:
            ag_id = int(re.sub(r"\D", "", str(dados["numero_agendamento"])))
            ag = db.query(Agendamento).filter(Agendamento.id == ag_id, Agendamento.empresa_id == empresa.id).first()
        except ValueError:
            pass
    elif dados.get("cliente_nome"):
        leads = buscar_lead_por_nome(db, empresa.id, dados["cliente_nome"])
        if len(leads) == 1:
            lead = leads[0]
            ag = db.query(Agendamento).filter(
                Agendamento.empresa_id == empresa.id,
                Agendamento.lead_id == lead.id
            ).order_by(Agendamento.criado_em.desc()).first()
            
    if ag:
        status_emoji = {
            "pendente": "⏳ Pendente",
            "confirmado": "✅ Confirmado",
            "recusado": "❌ Recusado",
            "cancelado": "⚠️ Cancelado"
        }.get(ag.status, ag.status)
        
        data_fmt = datetime.strptime(ag.data, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        lead_nome = ag.lead.nome if ag.lead else "Sem cliente associado"
        lead_tel = ag.lead.telefone if ag.lead else "N/A"
        
        res = (
            f"📋 *Agendamento #{ag.id}*\n"
            f"👤 *Cliente:* {lead_nome} ({lead_tel})\n"
            f"💼 *Serviço:* {ag.servico_nome} ({ag.servico_duracao} min)\n"
            f"📅 *Data:* {data_fmt} às {ag.hora_inicio}–{ag.hora_fim}\n"
            f"📍 *Endereço:* {ag.endereco or '[sem endereço]'}\n"
            f"📝 *Status:* {status_emoji}"
        )
        return {"status": "ok", "resposta": res}
    else:
        return {"status": "ok", "resposta": "⚠️ Não encontrei o agendamento solicitado."}

def processar_comando_cozinha(empresa: Empresa, mensagem_texto: str, telefone_auxiliar: str = None) -> dict:
    """
    Processador de comandos rápidos da cozinha/agenda via WhatsApp.
    Se for módulo agenda e tiver gatilho ou estado ativo, processa via NLP.
    Caso contrário, executa fluxo clássico da cozinha.
    """
    db = SessionLocal()
    try:
        texto = mensagem_texto.strip().lower()
        logger.info(f"[AUXILIAR/COZINHA] Mensagem recebida: '{texto}' de {telefone_auxiliar}")

        # 1. Verificar comandos rápidos de aprovação de agendamento: "[ID] confirmar" ou "[ID] recusar"
        match_quick_agenda = re.match(r'^(\d+)\s+(confirmar|recusar)(?:\s+(.+))?$', texto)
        if match_quick_agenda:
            agendamento_id = int(match_quick_agenda.group(1))
            acao = match_quick_agenda.group(2)
            motivo = match_quick_agenda.group(3) or ""
            
            from app.agenda_service import confirmar_agendamento, recusar_agendamento
            if acao == "confirmar":
                sucesso = confirmar_agendamento(db, agendamento_id)
                msg = f"✅ Agendamento #{agendamento_id} confirmado com sucesso!" if sucesso else f"⚠️ Não foi possível confirmar o agendamento #{agendamento_id}."
            else:
                sucesso = recusar_agendamento(db, agendamento_id, motivo)
                msg = f"❌ Agendamento #{agendamento_id} recusado com sucesso!" if sucesso else f"⚠️ Não foi possível recusar o agendamento #{agendamento_id}."
            return {"status": "ok", "resposta": msg}

        # 2. Carregar estado da agenda
        estado = carregar_estado_auxiliar(db, empresa.id)
        modulos = empresa.configuracoes.config.get("modulos_ativos", []) if empresa.configuracoes else []
        nicho = empresa.nicho
        has_agenda = "agenda" in modulos or nicho == "higienizacao"
        is_agenda_only = has_agenda and not ("lanchonete" in modulos)

        # 3. Se houver estado ativo da agenda, continuar fluxo de agenda
        if has_agenda and estado:
            import asyncio
            
            def run_async(coro):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                return loop.run_until_complete(coro)

            if estado.get("aguardando") == "confirmacao_agenda":
                dados = estado["dados_parciais"]
                confirmou = texto in ["sim", "s", "confirma", "confirmado", "ok", "pode", "isso", "vaih"]
                recusou = texto in ["nao", "não", "n", "cancelar", "para", "cancela"]
                
                if confirmou:
                    agendamento = criar_agendamento(
                        db,
                        empresa.id,
                        dados.get("lead_id"),
                        dados.get("servico_id"),
                        dados["data"],
                        dados["hora"],
                        dados.get("observacao") or "",
                        status="confirmado",
                        endereco=dados.get("endereco") or ""
                    )
                    if agendamento:
                        if dados.get("lead_id") and dados.get("sem_notificacao") is not True:
                            lead = db.query(Lead).filter(Lead.id == dados["lead_id"]).first()
                            if lead and lead.telefone:
                                config_agenda = empresa.configuracoes.config if empresa.configuracoes else {}
                                msg_cliente = montar_mensagem_confirmacao_cliente(agendamento, config_agenda)
                                try:
                                    enviar_whatsapp(lead.telefone, msg_cliente, empresa.evolution_instance)
                                except Exception as e:
                                    logger.error(f"Erro ao notificar cliente: {e}")
                        
                        limpar_estado_auxiliar(db, empresa.id)
                        return {"status": "ok", "resposta": f"✅ Agendamento #{agendamento.id} criado com sucesso e cliente notificado!"}
                    else:
                        limpar_estado_auxiliar(db, empresa.id)
                        return {"status": "ok", "resposta": "⚠️ Erro ao criar agendamento no banco de dados."}
                elif recusou:
                    limpar_estado_auxiliar(db, empresa.id)
                    return {"status": "ok", "resposta": "Ok, agendamento cancelado."}
                else:
                    return {"status": "ok", "resposta": "Não entendi. Responda 'sim' para confirmar ou 'não' para cancelar."}

            elif estado.get("aguardando") == "confirmacao_edicao":
                agendamento_id = estado["agendamento_id"]
                nova_data = estado["nova_data"]
                nova_hora = estado["nova_hora"]
                
                confirmou = texto in ["sim", "s", "confirma", "confirmado", "ok", "pode", "isso"]
                recusou = texto in ["nao", "não", "n", "cancelar", "para", "cancela"]
                
                if confirmou:
                    from app.database import Agendamento
                    ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
                    if ag:
                        from app.agenda_service import hm_to_min, min_to_hm
                        t_start = hm_to_min(nova_hora)
                        nova_hora_fim = min_to_hm(t_start + ag.servico_duracao)
                        
                        ag.data = nova_data
                        ag.hora_inicio = nova_hora
                        ag.hora_fim = nova_hora_fim
                        db.commit()
                        
                        if ag.lead_id:
                            lead = db.query(Lead).filter(Lead.id == ag.lead_id).first()
                            if lead and lead.telefone:
                                data_formatada = datetime.strptime(nova_data, '%Y-%m-%d').strftime('%d/%m/%Y')
                                msg_cli = (
                                    f"📅 *Seu agendamento foi reagendado!*\n\n"
                                    f"💼 *Serviço:* {ag.servico_nome}\n"
                                    f"📅 *Nova Data:* {data_formatada}\n"
                                    f"⏰ *Novo Horário:* {nova_hora} às {nova_hora_fim}\n\n"
                                    f"Qualquer dúvida, estamos à disposição."
                                )
                                try:
                                    enviar_whatsapp(lead.telefone, msg_cli, empresa.evolution_instance)
                                except Exception as e:
                                    logger.error(f"Erro ao notificar cliente do reagendamento: {e}")
                                    
                        limpar_estado_auxiliar(db, empresa.id)
                        return {"status": "ok", "resposta": f"✅ Agendamento #{ag.id} reagendado com sucesso!"}
                    else:
                        limpar_estado_auxiliar(db, empresa.id)
                        return {"status": "ok", "resposta": "⚠️ Agendamento não encontrado."}
                elif recusou:
                    limpar_estado_auxiliar(db, empresa.id)
                    return {"status": "ok", "resposta": "Reagendamento cancelado."}
                else:
                    return {"status": "ok", "resposta": "Não entendi. Responda 'sim' para confirmar ou 'não' para cancelar."}

            elif estado.get("aguardando") == "campo_agenda":
                campo = estado["campo"]
                dados = estado["dados_parciais"]
                
                if campo == "data":
                    from app.parser_data import parse_data
                    parsed_val = parse_data(mensagem_texto)
                    if parsed_val:
                        dados["data"] = parsed_val.strftime("%Y-%m-%d")
                    else:
                        return {"status": "ok", "resposta": "⚠️ Não consegui entender essa data. Por favor, envie novamente (ex: 25/11 ou 'amanhã')."}
                elif campo == "hora":
                    from app.parser_data import parse_hora
                    parsed_val = parse_hora(mensagem_texto)
                    if parsed_val:
                        dados["hora"] = parsed_val
                    else:
                        return {"status": "ok", "resposta": "⚠️ Não consegui entender esse horário. Por favor, envie novamente (ex: 14h ou 14:30)."}
                elif campo == "servico":
                    servico = buscar_servico_por_nome(db, empresa.id, mensagem_texto)
                    if servico:
                        dados["servico"] = servico.nome
                        dados["servico_id"] = str(servico.id)
                        dados["servico_duracao"] = servico.duracao_min
                        dados["servico_preco"] = servico.preco
                    else:
                        return {"status": "ok", "resposta": f"⚠️ Não encontrei nenhum serviço com esse nome. Digite novamente."}
                
                dados, faltando = validar_extracao(db, dados, empresa.id)
                return run_async(prosseguir_fluxo_agenda(db, empresa, dados, faltando, telefone_auxiliar))

            elif estado.get("aguardando") == "selecao_cliente":
                leads_ids = estado["leads_encontrados"]
                dados = estado["dados_parciais"]
                
                try:
                    escolha = int(texto.strip()) - 1
                    if 0 <= escolha < len(leads_ids):
                        dados["lead_id"] = leads_ids[escolha]
                        lead = db.query(Lead).filter(Lead.id == dados["lead_id"]).first()
                        if lead:
                            dados["cliente_nome"] = lead.nome
                            dados["cliente_telefone"] = lead.telefone
                        
                        dados, faltando = validar_extracao(db, dados, empresa.id)
                        return run_async(prosseguir_fluxo_agenda(db, empresa, dados, faltando, telefone_auxiliar))
                    else:
                        return {"status": "ok", "resposta": f"⚠️ Opção inválida. Escolha um número de 1 a {len(leads_ids)}."}
                except ValueError:
                    return {"status": "ok", "resposta": f"⚠️ Por favor, digite apenas o número da opção (1 a {len(leads_ids)})."}

            elif estado.get("aguardando") == "telefone_cliente":
                dados = estado["dados_parciais"]
                tel = re.sub(r"\D", "", mensagem_texto)
                if len(tel) >= 10:
                    if not tel.startswith("55"):
                        tel = "55" + tel
                    
                    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == tel).first()
                    if not lead:
                        lead = Lead(
                            empresa_id=empresa.id,
                            nome=dados.get("cliente_nome") or "Cliente Novo",
                            telefone=tel,
                            stage="agendado"
                        )
                        db.add(lead)
                        db.commit()
                        db.refresh(lead)
                    
                    dados["lead_id"] = str(lead.id)
                    dados["cliente_telefone"] = tel
                    dados["cliente_nome"] = lead.nome
                    
                    dados, faltando = validar_extracao(db, dados, empresa.id)
                    return run_async(prosseguir_fluxo_agenda(db, empresa, dados, faltando, telefone_auxiliar))
                else:
                    return {"status": "ok", "resposta": "⚠️ Telefone inválido. Por favor, envie o telefone com DDD (ex: 11999990000)."}

        # 4. Iniciar fluxo de agenda se tiver gatilho
        if has_agenda and tem_intencao_agenda(texto):
            import asyncio
            def run_async(coro):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                return loop.run_until_complete(coro)

            config = empresa.configuracoes.config if empresa.configuracoes else {}
            dados_llm = extrair_dados_agendamento(mensagem_texto, config, db)
            
            logger.info(f"[LLM AGENDA] Dados extraídos: {dados_llm}")
            
            if dados_llm.get("intencao") == "cancelar_agendamento":
                return processar_comando_cancelamento(db, empresa, dados_llm)
            elif dados_llm.get("intencao") == "editar_agendamento":
                return processar_comando_reagendamento(db, empresa, dados_llm)
            elif dados_llm.get("intencao") == "outro" and not dados_llm.get("servico") and not dados_llm.get("cliente_nome") and "detalhes" not in texto and "quando" not in texto:
                pass
            elif "detalhes" in texto or "quando" in texto or "compromisso" in texto:
                return processar_comando_detalhes(db, empresa, dados_llm)
            else:
                dados, faltando = validar_extracao(db, dados_llm, empresa.id)
                return run_async(prosseguir_fluxo_agenda(db, empresa, dados, faltando, telefone_auxiliar))

        # 5. Se for agenda_only e não bateu nos anteriores, mostra ajuda da agenda
        if is_agenda_only:
            help_agenda = (
                "🤖 *Assistente de Agenda - Menu do Profissional:*\n\n"
                "Você pode agendar, alterar ou cancelar compromissos usando linguagem natural (texto ou áudio).\n\n"
                "*Exemplos de comandos:*\n"
                "• _\"agenda faxina residencial para Maria amanhã às 14h na Rua das Flores 123\"_\n"
                "• _\"marcar higienização para João na sexta 9h\"_\n"
                "• _\"reagenda o #7 para sexta às 10h\"_\n"
                "• _\"cancela o agendamento da Maria na quinta\"_\n"
                "• _\"detalhes do #7\"_\n\n"
                "*Comandos rápidos de aprovação:*\n"
                "• `[número] confirmar` (ex: `7 confirmar`)\n"
                "• `[número] recusar [motivo]` (ex: `7 recusar Sem horários`)"
            )
            return {"status": "ok", "resposta": help_agenda}

        # 6. Fluxo clássico de lanchonete (cozinha)
        # 6.1 Comando: 'pedidos'
        if texto == "pedidos":
            pedidos_ativos = obter_pedidos_ativos(db, empresa.id)
            if not pedidos_ativos:
                return {"status": "ok", "resposta": "🍳 Não há nenhum pedido ativo em andamento no momento."}
                
            resposta_linhas = ["📋 *PEDIDOS ATIVOS EM ANDAMENTO:*"]
            for ped in pedidos_ativos:
                itens_resumo = ", ".join([f"{it.quantidade}x {it.nome}" for it in ped.itens])
                tipo_modo = "Delivery" if ped.modo == "delivery" else ("Mesa #" + str(ped.numero_mesa) if ped.modo == "mesa" else "Balcão")
                resposta_linhas.append(
                    f"• *Pedido #{ped.numero_pedido}* [{ped.status.upper()}] - {tipo_modo}\n"
                    f"  🛒 {itens_resumo} (R$ {ped.total:.2f})"
                )
            return {"status": "ok", "resposta": "\n".join(resposta_linhas)}

        # 6.2 Comando: 'cardapio'
        if texto == "cardapio":
            itens = listar_itens(db, empresa.id)
            if not itens:
                return {"status": "ok", "resposta": "🍔 O cardápio está vazio."}
                
            resposta_linhas = ["📋 *PRODUTOS DO CARDÁPIO:*"]
            for p in itens:
                status = "✅ Ativo" if p.disponivel else "❌ Pausado/Indisponível"
                resposta_linhas.append(f"• *{p.nome}* ({p.categoria}) - R$ {p.preco:.2f} | {status}")
            return {"status": "ok", "resposta": "\n".join(resposta_linhas)}

        # 6.3 Comando: 'pausar [item]'
        match_pausar = re.match(r'^pausar\s+(.+)$', texto)
        if match_pausar:
            item_nome = match_pausar.group(1).strip()
            item = obter_item_por_nome(db, empresa.id, item_nome)
            if not item:
                return {"status": "ok", "resposta": f"⚠️ Item '{item_nome}' não foi encontrado no cardápio."}
            item.disponivel = False
            db.commit()
            return {"status": "ok", "resposta": f"❌ *{item.nome}* foi pausado com sucesso e está indisponível para novos pedidos!"}

        # 6.4 Comando: 'ativar [item]'
        match_ativar = re.match(r'^ativar\s+(.+)$', texto)
        if match_ativar:
            item_nome = match_ativar.group(1).strip()
            item = obter_item_por_nome(db, empresa.id, item_nome)
            if not item:
                return {"status": "ok", "resposta": f"⚠️ Item '{item_nome}' não foi encontrado no cardápio."}
            item.disponivel = True
            db.commit()
            return {"status": "ok", "resposta": f"✅ *{item.nome}* foi ativado com sucesso e está disponível para novos pedidos!"}

        # 6.5 Comando: '[numero] tempo [minutos]'
        match_tempo = re.match(r'^(\d+)\s+tempo\s+(\d+)$', texto)
        if match_tempo:
            num_pedido = int(match_tempo.group(1))
            tempo_min = int(match_tempo.group(2))
            
            pedido = obter_pedido_por_numero(db, empresa.id, num_pedido)
            if not pedido:
                return {"status": "ok", "resposta": f"⚠️ Pedido #{num_pedido} não foi encontrado."}
                
            if pedido.status == "aguardando":
                pedido.status = "em_preparo"
                db.commit()
                
            if pedido.lead_id:
                lead = db.query(Lead).filter(Lead.id == pedido.lead_id).first()
                if lead and lead.telefone:
                    config = empresa.configuracoes.config if empresa.configuracoes else {}
                    nome_agente = config.get("nome_agente", "Rosana")
                    msg_cliente = (
                        f"Olá! Aqui é o(a) {nome_agente} da Piccolo Lanches. 👋\n\n"
                        f"🍳 *Seu pedido #{pedido.numero_pedido} já está sendo preparado!*\n"
                        f"⏱️ O tempo estimado de preparo para o seu pedido é de *{tempo_min} minutos*.\n\n"
                        f"Assim que sair da nossa cozinha, te avisaremos aqui! 😊"
                    )
                    try:
                        enviar_whatsapp(lead.telefone, msg_cliente, empresa.evolution_instance)
                    except Exception as e:
                        logger.error(f"Erro ao notificar tempo ao cliente: {e}")
                        
            return {"status": "ok", "resposta": f"⏱️ Tempo de *{tempo_min} min* definido para o Pedido #{num_pedido} e cliente notificado!"}

        # 6.6 Comandos rápidos de status: '[numero] [status]'
        match_status = re.match(r'^(\d+)\s+(ok|pronto|entregue|cancela|cancelado)$', texto)
        if match_status:
            num_pedido = int(match_status.group(1))
            cmd_status = match_status.group(2)
            
            pedido = obter_pedido_por_numero(db, empresa.id, num_pedido)
            if not pedido:
                return {"status": "ok", "resposta": f"⚠️ Pedido #{num_pedido} não foi encontrado."}
                
            status_map = {
                "ok": "em_preparo",
                "pronto": "pronto",
                "entregue": "entregue",
                "cancela": "cancelado",
                "cancelado": "cancelado"
            }
            novo_status = status_map[cmd_status]
            
            atualizar_status_pedido(db, pedido.id, novo_status)
            
            status_emoji = {
                "em_preparo": "🍳 em preparo",
                "pronto": "✅ pronto",
                "entregue": "📦 finalizado/entregue",
                "cancelado": "❌ cancelado"
            }
            
            return {
                "status": "ok", 
                "resposta": f"🚀 Pedido #{num_pedido} updated to *{status_emoji[novo_status].upper()}* com sucesso!"
            }

        # 6.7 Ajuda da Cozinha
        resposta_ajuda = (
            "🤖 *Piccolo Lanchonete - Menu da Cozinha:*\n\n"
            "Comandos rápidos para gerenciar pedidos ativos:\n"
            "• `pedidos` (listar todos os pedidos ativos)\n"
            "• `[número] ok` (iniciar preparo do pedido)\n"
            "• `[número] tempo [minutos]` (ex: `42 tempo 25`)\n"
            "• `[número] pronto` (pedido pronto / motoboy)\n"
            "• `[número] entregue` (finalizar pedido)\n"
            "• `[número] cancela` (cancelar pedido)\n\n"
            "Comandos para controle de cardápio:\n"
            "• `cardapio` (listar cardápio completo)\n"
            "• `pausar [nome do item]` (ex: `pausar X-Burguer`)\n"
            "• `ativar [nome do item]` (ex: `ativar X-Burguer`)"
        )
        return {"status": "ok", "resposta": resposta_ajuda}

    except Exception as e:
        logger.error(f"Erro fatal na pipeline de comando da cozinha: {e}", exc_info=True)
        return {"status": "erro", "motivo": str(e)}
    finally:
        db.close()
