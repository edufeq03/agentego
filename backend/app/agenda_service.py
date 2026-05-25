import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import pytz
from app.database import Servico, Disponibilidade, Bloqueio, Agendamento, Empresa, Lead
from app.whatsapp import enviar_whatsapp

logger = logging.getLogger(__name__)
TZ_SP = pytz.timezone('America/Sao_Paulo')

def hm_to_min(hm: str) -> int:
    """Converte 'HH:MM' em minutos a partir da meia-noite."""
    try:
        parts = hm.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def min_to_hm(m: int) -> str:
    """Converte minutos a partir da meia-noite em 'HH:MM'."""
    return f"{m // 60:02d}:{m % 60:02d}"

def obter_servicos_resolvidos(db: Session, empresa_id: Any, servico_id_input: Any, caracteristica: Optional[str] = None) -> List[dict]:
    """
    Dada uma entrada de servico_id (pode ser UUID único, string com múltiplos UUIDs separados por vírgula, ou lista de UUIDs),
    retorna a lista de dicionários correspondentes aos serviços encontrados,
    com a duração e o preço ajustados de acordo com a característica do cliente (se aplicável).
    """
    import uuid
    from app.database import Servico, Empresa
    
    ids_busca = []
    if isinstance(servico_id_input, list):
        ids_busca = servico_id_input
    elif isinstance(servico_id_input, str):
        if servico_id_input.startswith("[") and servico_id_input.endswith("]"):
            try:
                import json
                ids_busca = json.loads(servico_id_input)
            except Exception:
                ids_busca = [x.strip() for x in servico_id_input.split(",") if x.strip()]
        else:
            ids_busca = [x.strip() for x in servico_id_input.split(",") if x.strip()]
    else:
        ids_busca = [servico_id_input]

    resolvidos = []
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    config_dict = empresa.configuracoes.config if (empresa and empresa.configuracoes) else {}

    for sid in ids_busca:
        try:
            if isinstance(sid, str):
                uuid.UUID(sid)
        except ValueError:
            continue

        s = db.query(Servico).filter(Servico.id == sid, Servico.ativo == True).first()
        if not s:
            continue
            
        duracao = s.duracao_min
        preco = s.preco
        
        if caracteristica:
            # 1. Verifica no campo 'caracteristicas' do próprio serviço (JSONB)
            has_service_override = False
            if getattr(s, "tem_variacao_caracteristica", False) and getattr(s, "caracteristicas", None) and isinstance(s.caracteristicas, dict):
                regras = s.caracteristicas.get(caracteristica)
                if regras and isinstance(regras, dict):
                    dur_override = regras.get("duracao") or regras.get("duracao_min")
                    if dur_override is not None:
                        duracao = int(dur_override)
                        has_service_override = True
                    preco_override = regras.get("preco")
                    if preco_override is not None:
                        preco = float(preco_override)
                        has_service_override = True
            
            # 2. Caso contrário, busca na configuração global da empresa
            if not has_service_override and config_dict:
                dur_override = config_dict.get("duracao_por_caracteristica", {}).get(s.nome, {}).get(caracteristica)
                if dur_override is not None:
                    duracao = int(dur_override)
                preco_override = config_dict.get("preco_por_caracteristica", {}).get(s.nome, {}).get(caracteristica)
                if preco_override is not None:
                    preco = float(preco_override)
                
        resolvidos.append({
            "id": s.id,
            "nome": s.nome,
            "duracao_min": duracao,
            "preco": preco,
            "cor": s.cor
        })
        
    return resolvidos

def obter_duracao_preco_servico(db: Session, empresa_id: Any, servico_id: Any, caracteristica: Optional[str] = None) -> tuple[int, Optional[float]]:
    resolvidos = obter_servicos_resolvidos(db, empresa_id, servico_id, caracteristica)
    if not resolvidos:
        return 0, None
    total_duracao = sum(r["duracao_min"] for r in resolvidos)
    total_preco = sum(r["preco"] for r in resolvidos if r["preco"] is not None)
    tem_preco = any(r["preco"] is not None for r in resolvidos)
    final_preco = total_preco if tem_preco else None
    return total_duracao, final_preco

def calcular_slots(db: Session, empresa_id: Any, servico_id: Any, data_str: str, caracteristica: Optional[str] = None) -> List[str]:
    """
    Calcula os slots de horários disponíveis para agendamento.
    Leva em consideração:
    1. Horários de funcionamento padrão da empresa para o dia da semana.
    2. Duração do serviço (e se há múltiplos serviços ou variação por característica).
    3. Bloqueios específicos de horários na data.
    4. Agendamentos existentes (status 'confirmado' ou 'pendente').
    5. Se for a data atual, remove horários passados.
    """
    try:
        # 1. Obter serviço / serviços resolvidos e soma de durações
        resolvidos = obter_servicos_resolvidos(db, empresa_id, servico_id, caracteristica)
        if not resolvidos:
            logger.warning(f"Nenhum serviço válido encontrado para cálculo de slots: {servico_id}")
            return []
            
        duracao = sum(r["duracao_min"] for r in resolvidos)
        
        # 2. Obter dia da semana (0=Segunda, 6=Domingo)
        data_parsed = datetime.strptime(data_str, "%Y-%m-%d").date()
        dia_semana = data_parsed.weekday()
        
        # 3. Carregar disponibilidade da empresa para este dia da semana
        disps = db.query(Disponibilidade).filter(
            Disponibilidade.empresa_id == empresa_id,
            Disponibilidade.dia_semana == dia_semana,
            Disponibilidade.ativo == True
        ).all()
        
        if not disps:
            # Fallback: se a empresa não tem NENHUMA disponibilidade cadastrada no BD,
            # oferece um padrão de Segunda a Sexta das 09:00 às 18:00
            has_any_config = db.query(Disponibilidade).filter(
                Disponibilidade.empresa_id == empresa_id
            ).first() is not None
            
            if not has_any_config and dia_semana in [0, 1, 2, 3, 4]:
                class TempDisp:
                    def __init__(self, dia, inicio, fim, intervalo, ativo):
                        self.dia_semana = dia
                        self.hora_inicio = inicio
                        self.hora_fim = fim
                        self.intervalo_min = intervalo
                        self.ativo = ativo
                disps = [TempDisp(dia_semana, "09:00", "18:00", 30, True)]
            else:
                return []
            
        # 4. Carregar bloqueios para a data
        bloqueios = db.query(Bloqueio).filter(
            Bloqueio.empresa_id == empresa_id,
            Bloqueio.data == data_str
        ).all()
        
        bloqueios_min = []
        for b in bloqueios:
            bloqueios_min.append((hm_to_min(b.hora_inicio), hm_to_min(b.hora_fim)))
            
        # 5. Carregar agendamentos existentes (status 'confirmado' ou 'pendente')
        agendamentos = db.query(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data == data_str,
            Agendamento.status.in_(['confirmado', 'pendente'])
        ).all()
        
        agendamentos_min = []
        for a in agendamentos:
            agendamentos_min.append((hm_to_min(a.hora_inicio), hm_to_min(a.hora_fim)))

        # 6. Obter hora atual se for hoje
        hoje_local = datetime.now(TZ_SP)
        agora_min = hoje_local.hour * 60 + hoje_local.minute if hoje_local.date() == data_parsed else None

        slots_disponiveis = []

        # 7. Gerar e filtrar slots
        for disp in disps:
            t_start = hm_to_min(disp.hora_inicio)
            t_end = hm_to_min(disp.hora_fim)
            intervalo = disp.intervalo_min if disp.intervalo_min > 0 else 30
            
            t = t_start
            while t <= (t_end - duracao):
                t_slot_start = t
                t_slot_end = t + duracao
                
                # Regra 1: Não pode ser no passado (se for hoje)
                if agora_min is not None and t_slot_start <= agora_min:
                    t += intervalo
                    continue
                    
                # Regra 2: Conflito com Bloqueios
                conflito_bloqueio = False
                for b_start, b_end in bloqueios_min:
                    # Sobreposição: slot começa antes do fim do bloqueio e termina após o início do bloqueio
                    if t_slot_start < b_end and t_slot_end > b_start:
                        conflito_bloqueio = True
                        break
                if conflito_bloqueio:
                    t += intervalo
                    continue
                    
                # Regra 3: Conflito com outros agendamentos
                conflito_agendamento = False
                for a_start, a_end in agendamentos_min:
                    # Sobreposição
                    if t_slot_start < a_end and t_slot_end > a_start:
                        conflito_agendamento = True
                        break
                if conflito_agendamento:
                    t += intervalo
                    continue
                
                # Se passou em todas as regras, o slot está livre
                slots_disponiveis.append(min_to_hm(t_slot_start))
                t += intervalo
                
        return slots_disponiveis
    except Exception as e:
        logger.error(f"Erro ao calcular slots para empresa={empresa_id}, servico={servico_id}, data={data_str}: {e}")
        return []

def criar_agendamento_cliente(db: Session, empresa_id: Any, lead_id: Any, servico_id: Any, data_str: str, hora_inicio: str, observacao: str = "", endereco: str = "", caracteristica: Optional[str] = None) -> Agendamento | None:
    """
    Cria um agendamento com status 'pendente' e envia notificação de aprovação manual para o profissional.
    """
    try:
        # Resolve todos os serviços
        resolvidos = obter_servicos_resolvidos(db, empresa_id, servico_id, caracteristica)
        if not resolvidos:
            raise ValueError("Nenhum serviço válido encontrado.")
            
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead/Cliente não encontrado.")
            
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise ValueError("Empresa não encontrada.")

        # Valida se o slot está de fato livre (prevenção contra concorrência/duplo clique)
        slots_livres = calcular_slots(db, empresa_id, servico_id, data_str, caracteristica)
        if hora_inicio not in slots_livres:
            logger.warning(f"Slot {hora_inicio} não disponível para data {data_str}")
            return None

        # Calcula a duração total
        duracao_total = sum(r["duracao_min"] for r in resolvidos)
        t_start = hm_to_min(hora_inicio)
        hora_fim = min_to_hm(t_start + duracao_total)
        
        nomes_servicos = " + ".join(r["nome"] for r in resolvidos)

        # Prepara a observação com característica
        obs_completa = observacao
        if caracteristica:
            obs_completa = f"Característica: {caracteristica}\n{observacao}" if observacao else f"Característica: {caracteristica}"

        # Cria o agendamento
        agendamento = Agendamento(
            empresa_id=empresa_id,
            lead_id=lead_id,
            servico_id=resolvidos[0]["id"],
            servico_nome=nomes_servicos,
            servico_duracao=duracao_total,
            data=data_str,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            status='pendente',
            observacao=obs_completa,
            endereco=endereco
        )
        db.add(agendamento)
        db.commit()
        db.refresh(agendamento)

        # Cria os itens do agendamento
        from app.database import ItemAgendamento
        for r in resolvidos:
            item = ItemAgendamento(
                agendamento_id=agendamento.id,
                servico_id=r["id"],
                servico_nome=r["nome"],
                duracao_min=r["duracao_min"],
                preco=r["preco"]
            )
            db.add(item)
        db.commit()

        # Notifica o profissional para aprovação manual se configurado
        config_agenda = empresa.configuracoes.config.get("agenda", {}) if empresa.configuracoes else {}
        aprovacao_manual = config_agenda.get("aprovacao_manual", True)
        whatsapp_profissional = config_agenda.get("whatsapp_profissional")

        if aprovacao_manual and whatsapp_profissional:
            # Envia mensagem para o profissional
            endereco_txt = f"\n📍 *Endereço:* {endereco}" if endereco else ""
            mensagem_prof = (
                f"🚨 *NOVA SOLICITAÇÃO DE AGENDAMENTO (ID: {agendamento.id})*\n\n"
                f"👤 *Cliente:* {lead.nome} ({lead.telefone})\n"
                f"💼 *Serviço:* {nomes_servicos}\n"
                f"📅 *Data:* {datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')}\n"
                f"⏰ *Horário:* {hora_inicio} às {hora_fim}{endereco_txt}\n"
                f"📝 *Obs:* {obs_completa or 'Nenhuma'}\n\n"
                f"Para responder, envie:\n"
                f"👉 *{agendamento.id} confirmar* (para aceitar)\n"
                f"👉 *{agendamento.id} recusar* (para rejeitar)\n"
            )
            # Envia usando a instância do WhatsApp associada à empresa
            enviar_whatsapp(
                whatsapp_profissional,
                mensagem_prof,
                empresa.evolution_instance or empresa.slug
            )
            logger.info(f"Notificação de aprovação do agendamento {agendamento.id} enviada ao profissional {whatsapp_profissional}")
        else:
            # Aprovação automática caso desabilitado manual
            confirmar_agendamento(db, agendamento.id)

        return agendamento
    except Exception as e:
        logger.error(f"Erro ao criar agendamento para empresa={empresa_id}: {e}")
        db.rollback()
        return None

def criar_agendamento(db: Session, empresa_id: Any, lead_id: Any, servico_id: Any, data_str: str, hora_inicio: str, observacao: str = "", status: str = "pendente", endereco: str = "", caracteristica: Optional[str] = None) -> Agendamento | None:
    try:
        # Resolve todos os serviços
        resolvidos = obter_servicos_resolvidos(db, empresa_id, servico_id, caracteristica)
        if not resolvidos:
            raise ValueError("Nenhum serviço válido encontrado.")
            
        lead = None
        if lead_id:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise ValueError("Empresa não encontrada.")

        # Calcula a duração total
        duracao_total = sum(r["duracao_min"] for r in resolvidos)
        t_start = hm_to_min(hora_inicio)
        hora_fim = min_to_hm(t_start + duracao_total)
        
        nomes_servicos = " + ".join(r["nome"] for r in resolvidos)

        # Prepara a observação com característica
        obs_completa = observacao
        if caracteristica:
            obs_completa = f"Característica: {caracteristica}\n{observacao}" if observacao else f"Característica: {caracteristica}"

        agendamento = Agendamento(
            empresa_id=empresa_id,
            lead_id=lead_id,
            servico_id=resolvidos[0]["id"],
            servico_nome=nomes_servicos,
            servico_duracao=duracao_total,
            data=data_str,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            status=status,
            observacao=obs_completa,
            endereco=endereco
        )
        db.add(agendamento)
        db.commit()
        db.refresh(agendamento)

        # Cria os itens do agendamento
        from app.database import ItemAgendamento
        for r in resolvidos:
            item = ItemAgendamento(
                agendamento_id=agendamento.id,
                servico_id=r["id"],
                servico_nome=r["nome"],
                duracao_min=r["duracao_min"],
                preco=r["preco"]
            )
            db.add(item)
        db.commit()

        if status == 'confirmado' and lead:
            lead.stage = 'agendado'
            db.commit()

        return agendamento
    except Exception as e:
        logger.error(f"Erro ao criar agendamento direto: {e}")
        db.rollback()
        return None

def buscar_agendamento_por_cliente_data(db: Session, empresa_id: Any, lead_id: Any, data_str: str) -> Agendamento | None:
    try:
        return db.query(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.lead_id == lead_id,
            Agendamento.data == data_str,
            Agendamento.status.in_(['confirmado', 'pendente'])
        ).order_by(Agendamento.criado_em.desc()).first()
    except Exception as e:
        logger.error(f"Erro ao buscar agendamento: {e}")
        return None

def confirmar_agendamento(db: Session, agendamento_id: int) -> bool:
    """Confirma um agendamento e avisa o cliente."""
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
        if not agendamento:
            return False
        if agendamento.status == 'confirmado':
            return True
        if agendamento.status != 'pendente':
            return False
            
        agendamento.status = 'confirmado'
        db.commit()
        
        # Carrega dados adicionais para a mensagem
        lead = db.query(Lead).filter(Lead.id == agendamento.lead_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == agendamento.empresa_id).first()
        
        if lead and empresa:
            data_formatada = datetime.strptime(agendamento.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            msg_cliente = (
                f"✅ *Seu agendamento foi confirmado!*\n\n"
                f"💼 *Serviço:* {agendamento.servico_nome}\n"
                f"📅 *Data:* {data_formatada}\n"
                f"⏰ *Horário:* {agendamento.hora_inicio}\n\n"
                f"Aguardamos você! Qualquer dúvida, estamos à disposição."
            )
            enviar_whatsapp(
                lead.telefone,
                msg_cliente,
                empresa.evolution_instance or empresa.slug
            )
            
            # Atualiza o funil de vendas do Lead para 'agendado'
            lead.stage = 'agendado'
            db.commit()
            
        return True
    except Exception as e:
        logger.error(f"Erro ao confirmar agendamento {agendamento_id}: {e}")
        db.rollback()
        return False

def recusar_agendamento(db: Session, agendamento_id: int, motivo: str = "") -> bool:
    """Recusa um agendamento pendente e avisa o cliente."""
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
        if not agendamento or agendamento.status != 'pendente':
            return False
            
        agendamento.status = 'recusado'
        agendamento.motivo_cancelamento = motivo
        db.commit()
        
        lead = db.query(Lead).filter(Lead.id == agendamento.lead_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == agendamento.empresa_id).first()
        
        if lead and empresa:
            data_formatada = datetime.strptime(agendamento.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            motivo_txt = f"\n*Motivo:* {motivo}" if motivo else ""
            msg_cliente = (
                f"❌ *Infelizmente, seu pedido de agendamento não pôde ser aceito.*\n\n"
                f"💼 *Serviço:* {agendamento.servico_nome}\n"
                f"📅 *Data:* {data_formatada}\n"
                f"⏰ *Horário:* {agendamento.hora_inicio}{motivo_txt}\n\n"
                f"Você pode tentar escolher outro dia ou horário. Digite *agendar* para reiniciar."
            )
            enviar_whatsapp(
                lead.telefone,
                msg_cliente,
                empresa.evolution_instance or empresa.slug
            )
            
        return True
    except Exception as e:
        logger.error(f"Erro ao recusar agendamento {agendamento_id}: {e}")
        db.rollback()
        return False

def cancelar_agendamento(db: Session, agendamento_id: int, motivo: str = "") -> bool:
    """Cancela um agendamento confirmado ou pendente e avisa as partes."""
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
        if not agendamento or agendamento.status in ('cancelado', 'recusado'):
            return False
            
        origem_status = agendamento.status
        agendamento.status = 'cancelado'
        agendamento.motivo_cancelamento = motivo
        db.commit()
        
        lead = db.query(Lead).filter(Lead.id == agendamento.lead_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == agendamento.empresa_id).first()
        
        if lead and empresa:
            data_formatada = datetime.strptime(agendamento.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            motivo_txt = f"\n*Motivo:* {motivo}" if motivo else ""
            msg_cliente = (
                f"⚠️ *Seu agendamento foi cancelado.*\n\n"
                f"💼 *Serviço:* {agendamento.servico_nome}\n"
                f"📅 *Data:* {data_formatada}\n"
                f"⏰ *Horário:* {agendamento.hora_inicio}{motivo_txt}\n\n"
                f"Se precisar reagendar, basta enviar *agendar* novamente."
            )
            enviar_whatsapp(
                lead.telefone,
                msg_cliente,
                empresa.evolution_instance or empresa.slug
            )
            
            # Avisa o profissional se já estava confirmado
            if origem_status == 'confirmado':
                config_agenda = empresa.configuracoes.config.get("agenda", {}) if empresa.configuracoes else {}
                whatsapp_profissional = config_agenda.get("whatsapp_profissional")
                if whatsapp_profissional:
                    msg_prof = (
                        f"⚠️ *AGENDAMENTO CANCELADO (ID: {agendamento.id})*\n\n"
                        f"👤 *Cliente:* {lead.nome}\n"
                        f"💼 *Serviço:* {agendamento.servico_nome}\n"
                        f"📅 *Data:* {data_formatada}\n"
                        f"⏰ *Horário:* {agendamento.hora_inicio}{motivo_txt}\n"
                    )
                    enviar_whatsapp(
                        whatsapp_profissional,
                        msg_prof,
                        empresa.evolution_instance or empresa.slug
                    )
            
        # Dispara verificação de lista de espera
        try:
            if agendamento:
                config_features = empresa.configuracoes.config.get("features", {}) if (empresa and empresa.configuracoes) else {}
                if config_features.get("lista_espera", False):
                    job_verificar_lista_espera(db, agendamento.empresa_id, agendamento.servico_id, agendamento.data)
        except Exception as e:
            logger.error(f"Erro ao verificar lista de espera ao cancelar agendamento {agendamento_id}: {e}")

        return True
    except Exception as e:
        logger.error(f"Erro ao cancelar agendamento {agendamento_id}: {e}")
        db.rollback()
        return False

def tarefa_processar_agenda():
    """
    Tarefa de segundo plano (APScheduler) executada periodicamente.
    """
    from app.database import SessionLocal, Lead, Empresa, Agendamento
    from sqlalchemy.orm.attributes import flag_modified
    
    db = SessionLocal()
    try:
        agora = datetime.now(TZ_SP)
        hoje_str = agora.strftime("%Y-%m-%d")
        
        # 1. PROCESSAR TIMEOUTS DE AGENDAMENTOS PENDENTES
        agendamentos_pendentes = db.query(Agendamento).filter(Agendamento.status == 'pendente').all()
        for a in agendamentos_pendentes:
            empresa = db.query(Empresa).filter(Empresa.id == a.empresa_id).first()
            if not empresa:
                continue
            config_agenda = empresa.configuracoes.config.get("agenda", {}) if empresa.configuracoes else {}
            timeout_min = config_agenda.get("aprovacao_timeout_min", 60)
            
            if a.criado_em:
                criado_utc = pytz.utc.localize(a.criado_em)
                criado_local = criado_utc.astimezone(TZ_SP)
                diferenca = (agora - criado_local).total_seconds() / 60
                
                if diferenca >= timeout_min:
                    logger.info(f"Cancelando agendamento #{a.id} por timeout ({diferenca:.1f} min)")
                    recusar_agendamento(db, a.id, f"Solicitação expirada (tempo limite de {timeout_min} min excedido).")

        # 2. DISPARAR LEMBRETES DE AGENDAMENTOS CONFIRMADOS
        agendamentos_hoje = db.query(Agendamento).filter(
            Agendamento.status == 'confirmado',
            Agendamento.data == hoje_str,
            Agendamento.lembrete_cliente_enviado == False
        ).all()
        
        for a in agendamentos_hoje:
            empresa = db.query(Empresa).filter(Empresa.id == a.empresa_id).first()
            if not empresa:
                continue
            config_agenda = empresa.configuracoes.config.get("agenda", {}) if empresa.configuracoes else {}
            lembrete_min = config_agenda.get("lembrete_cliente_min", 120)
            
            try:
                dt_slot = TZ_SP.localize(datetime.strptime(f"{a.data} {a.hora_inicio}", "%Y-%m-%d %H:%M"))
                diferenca_min = (dt_slot - agora).total_seconds() / 60
                
                if 0 < diferenca_min <= lembrete_min:
                    lead = db.query(Lead).filter(Lead.id == a.lead_id).first()
                    if lead:
                        msg_lembrete = (
                            f"⏰ *Lembrete de Agendamento!*\n\n"
                            f"Olá, {lead.nome}!\n"
                            f"Passando para lembrar que você tem um horário agendado hoje.\n\n"
                            f"💼 *Serviço:* {a.servico_nome}\n"
                            f"⏰ *Horário:* {a.hora_inicio}\n\n"
                            f"Se precisar alterar ou cancelar, por favor nos avise com antecedência!"
                        )
                        enviar_whatsapp(
                            lead.telefone,
                            msg_lembrete,
                            empresa.evolution_instance or empresa.slug
                        )
                        a.lembrete_cliente_enviado = True
                        db.commit()
                        logger.info(f"Lembrete enviado para o cliente {lead.telefone} referente ao agendamento #{a.id}")
            except Exception as e:
                logger.error(f"Erro ao processar lembrete para agendamento #{a.id}: {e}")

        # 3. DISPARAR RESUMO DIÁRIO PARA O PROFISSIONAL
        empresas = db.query(Empresa).all()
        for emp in empresas:
            config_agenda = emp.configuracoes.config.get("agenda", {}) if emp.configuracoes else {}
            modulos = emp.configuracoes.config.get("modulos_ativos", []) if emp.configuracoes else []
            if "agenda" not in modulos and emp.nicho != "agenda" and emp.nicho != "higienizacao":
                continue
                
            whatsapp_prof = config_agenda.get("whatsapp_profissional") or config_agenda.get("whatsapp_professional")
            if not whatsapp_prof:
                continue
                
            hora_resumo_str = config_agenda.get("lembrete_profissional_hora", "08:00")
            resumo_enviado = config_agenda.get("resumo_diario_enviado_data")
            if resumo_enviado == hoje_str:
                continue
                
            try:
                hora_partes = hora_resumo_str.split(":")
                hora_resumo = agora.replace(hour=int(hora_partes[0]), minute=int(hora_partes[1]), second=0, microsecond=0)
                if agora >= hora_resumo:
                    agendas_hoje = db.query(Agendamento).filter(
                        Agendamento.empresa_id == emp.id,
                        Agendamento.data == hoje_str,
                        Agendamento.status == 'confirmado'
                    ).order_by(Agendamento.hora_inicio.asc()).all()
                    
                    if agendas_hoje:
                        linhas = []
                        for i, ag in enumerate(agendas_hoje, 1):
                            lead = db.query(Lead).filter(Lead.id == ag.lead_id).first()
                            cliente_nome = lead.nome if lead else "Cliente"
                            linhas.append(f"{i}. *{ag.hora_inicio}* - {cliente_nome} ({ag.servico_nome})")
                        
                        msg_resumo = (
                            f"📅 *RESUMO DOS AGENDAMENTOS DE HOJE ({agora.strftime('%d/%m/%Y')})*\n\n" +
                            "\n".join(linhas) + "\n\n"
                            f"Tenha um ótimo dia de trabalho! 💼"
                        )
                    else:
                        msg_resumo = f"📅 *RESUMO DE HOJE ({agora.strftime('%d/%m/%Y')})*\n\nVocê não possui agendamentos confirmados para hoje."
                        
                    enviar_whatsapp(
                        whatsapp_prof,
                        msg_resumo,
                        emp.evolution_instance or emp.slug
                    )
                    
                    config_data = dict(emp.configuracoes.config) if emp.configuracoes else {}
                    if "agenda" not in config_data:
                        config_data["agenda"] = {}
                    config_data["agenda"]["resumo_diario_enviado_data"] = hoje_str
                    emp.configuracoes.config = config_data
                    flag_modified(emp.configuracoes, "config")
                    db.commit()
                    logger.info(f"Resumo diário enviado ao profissional da empresa {emp.nome}")
            except Exception as e:
                logger.error(f"Erro ao processar resumo diário para profissional da empresa {emp.id}: {e}")

    except Exception as e:
        logger.error(f"Erro ao processar tarefa_processar_agenda: {e}")
    finally:
        db.close()

def job_verificar_lista_espera(db: Session, empresa_id: Any, servico_id: Any, data: str):
    """
    Verifica se há alguém na lista de espera para o serviço e data indicados,
    e notifica o primeiro da fila se houver um slot livre.
    """
    from app.database import ListaEspera, Lead
    
    espectadores = db.query(ListaEspera).filter(
        ListaEspera.empresa_id == empresa_id,
        ListaEspera.servico_id == servico_id,
        ListaEspera.data == data,
        ListaEspera.status == 'aguardando'
    ).order_by(ListaEspera.posicao.asc()).all()
    
    if not espectadores:
        return
        
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        return
        
    config = empresa.configuracoes.config if empresa.configuracoes else {}
    
    slots = calcular_slots(db, empresa_id, servico_id, data)
    if not slots:
        return
        
    proximo = espectadores[0]
    hora_vaga = slots[0]
    
    msg_template = config.get("mensagens", {}).get(
        "lista_espera_aviso",
        "🔔 Boa notícia! Abriu uma vaga para {servico} no dia {data} às {hora}. Quer confirmar?"
    )
    
    try:
        data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        data_formatada = data
        
    msg = msg_template.format(
        servico=proximo.servico.nome,
        data=data_formatada,
        hora=hora_vaga
    )
    
    enviar_whatsapp(
        proximo.lead.telefone,
        msg,
        empresa.evolution_instance or empresa.slug
    )
    
    proximo.status = 'notificado'
    proximo.notificado_em = datetime.utcnow()
    db.commit()
    
    dados_custom = proximo.lead.dados_customizados or {}
    if not isinstance(dados_custom, dict):
        dados_custom = {}
    dados_custom["agenda_estado"] = "aguardando_confirmacao_lista_espera"
    dados_custom["lista_espera_id"] = proximo.id
    dados_custom["lista_espera_hora"] = hora_vaga
    dados_custom["lista_espera_data"] = data
    dados_custom["lista_espera_servico_id"] = str(servico_id)
    proximo.lead.dados_customizados = dados_custom
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(proximo.lead, "dados_customizados")
    db.commit()
    
    logger.info(f"Lista de espera: Lead {proximo.lead.nome} ({proximo.lead.telefone}) notificado para vaga no dia {data} às {hora_vaga}")

def job_expirar_lista_espera():
    """
    Expira notificações da lista de espera sem resposta por mais de 30 minutos.
    Avisa o próximo da fila.
    """
    from app.database import SessionLocal, ListaEspera
    db = SessionLocal()
    try:
        limite = datetime.utcnow() - timedelta(minutes=30)
        expirados = db.query(ListaEspera).filter(
            ListaEspera.status == 'notificado',
            ListaEspera.notificado_em < limite
        ).all()
        
        for item in expirados:
            logger.info(f"Expirando vaga da lista de espera para registro {item.id} (Lead {item.lead.nome})")
            item.status = 'expirado'
            db.commit()
            
            dados_custom = item.lead.dados_customizados or {}
            if dados_custom.get("agenda_estado") == "aguardando_confirmacao_lista_espera":
                dados_custom["agenda_estado"] = "inicio"
                item.lead.dados_customizados = dados_custom
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(item.lead, "dados_customizados")
                db.commit()
            
            job_verificar_lista_espera(db, item.empresa_id, item.servico_id, item.data)
            
    except Exception as e:
        logger.error(f"Erro no job_expirar_lista_espera: {e}")
    finally:
        db.close()
