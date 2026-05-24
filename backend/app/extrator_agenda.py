import re
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.openai_client import client as cliente_openai
from app.database import Servico, Lead

logger = logging.getLogger(__name__)

PROMPT_EXTRACAO_AGENDA = """
Você é um extrator de dados de agendamento. Analise a mensagem e retorne
APENAS um JSON válido, sem texto antes ou depois.

Data de hoje: {data_hoje}
Dia da semana hoje: {dia_semana_hoje}
Serviços disponíveis: {lista_servicos}

Extraia os seguintes campos da mensagem:
{{
  "intencao": "criar_agendamento" | "editar_agendamento" | "cancelar_agendamento" | "outro",
  "servico": "nome do serviço ou null",
  "cliente_nome": "nome do cliente ou null",
  "cliente_telefone": "telefone formatado (só números) ou null",
  "data": "YYYY-MM-DD ou null",
  "hora": "HH:MM ou null",
  "endereco": "endereço completo ou null",
  "numero_agendamento": "número do agendamento para editar/cancelar ou null",
  "observacao": "observações extras ou null",
  "sem_notificacao": false
}}

Regras:
- "amanhã" = {data_amanha}
- "semana que vem" = próxima segunda-feira = {proxima_segunda}
- "próxima [dia]" = o [dia] da semana que vem
- Se o serviço não bater exatamente, escolha o mais próximo da lista
- Telefone: remover parênteses, traços, espaços. Adicionar 55 no DDI se for celular brasileiro sem DDI e não tiver.
- Se intencao for "outro" → todos os outros campos podem ser null
"""

def carregar_servicos(db: Session, empresa_id: Any) -> List[Dict[str, Any]]:
    servicos = db.query(Servico).filter(Servico.empresa_id == empresa_id, Servico.ativo == True).all()
    return [{"id": str(s.id), "nome": s.nome, "duracao_min": s.duracao_min, "preco": s.preco} for s in servicos]

def extrair_dados_agendamento(mensagem: str, config: dict, db: Session) -> dict:
    try:
        hoje = date.today()
        data_amanha = hoje + timedelta(days=1)
        proxima_seg = hoje + timedelta(days=(7 - hoje.weekday()))

        servicos = carregar_servicos(db, config["id"])
        lista_servicos = ", ".join([s["nome"] for s in servicos])

        prompt = PROMPT_EXTRACAO_AGENDA.format(
            data_hoje=hoje.strftime("%Y-%m-%d"),
            dia_semana_hoje=["segunda","terça","quarta","quinta",
                             "sexta","sábado","domingo"][hoje.weekday()],
            data_amanha=data_amanha.strftime("%Y-%m-%d"),
            proxima_segunda=proxima_seg.strftime("%Y-%m-%d"),
            lista_servicos=lista_servicos,
        )

        resposta = cliente_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",   "content": mensagem},
            ],
            temperature=0,
            max_tokens=300,
        )

        texto = resposta.choices[0].message.content.strip()
        texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        return json.loads(texto)
    except Exception as e:
        logger.error(f"Erro ao extrair dados de agendamento via LLM: {e}")
        return {"intencao": "outro"}

def buscar_servico_por_nome(db: Session, empresa_id: Any, nome_pesquisa: str):
    if not nome_pesquisa:
        return None
    servicos = db.query(Servico).filter(Servico.empresa_id == empresa_id, Servico.ativo == True).all()
    
    from difflib import get_close_matches
    nomes = [s.nome for s in servicos]
    matches = get_close_matches(nome_pesquisa, nomes, n=1, cutoff=0.3)
    if matches:
        nome_match = matches[0]
        for s in servicos:
            if s.nome == nome_match:
                return s
                
    for s in servicos:
        if nome_pesquisa.lower() in s.nome.lower() or s.nome.lower() in nome_pesquisa.lower():
            return s
            
    return None

def validar_extracao(db: Session, dados: dict, empresa_id: Any) -> Tuple[dict, List[str]]:
    faltando = []

    # 1. Serviço
    if not dados.get("servico"):
        faltando.append("servico")
    else:
        servico = buscar_servico_por_nome(db, empresa_id, dados["servico"])
        if not servico:
            faltando.append("servico")
        else:
            dados["servico_id"] = str(servico.id)
            dados["servico_duracao"] = servico.duracao_min
            dados["servico_preco"] = servico.preco
            dados["servico"] = servico.nome

    # 2. Data
    if not dados.get("data"):
        faltando.append("data")
    else:
        try:
            val_date = date.fromisoformat(dados["data"])
            if val_date < date.today():
                faltando.append("data_passada")
        except ValueError:
            faltando.append("data")

    # 3. Hora
    if not dados.get("hora"):
        faltando.append("hora")
    elif dados.get("data") and dados.get("servico_id"):
        from app.agenda_service import calcular_slots
        slots = calcular_slots(db, empresa_id, dados["servico_id"], dados["data"])
        if dados["hora"] not in slots:
            # Tentar normalizar formato HH:MM
            hora_norm = dados["hora"]
            if len(hora_norm) == 4 and ":" in hora_norm:
                hora_norm = "0" + hora_norm
            if hora_norm in slots:
                dados["hora"] = hora_norm
            else:
                faltando.append("hora_indisponivel")

    return dados, faltando

def buscar_lead_por_nome(db: Session, empresa_id: Any, nome_parcial: str) -> List[Lead]:
    if not nome_parcial:
        return []
    return db.query(Lead).filter(
        Lead.empresa_id == empresa_id,
        Lead.nome.ilike(f"%{nome_parcial}%")
    ).order_by(Lead.atualizado_em.desc()).limit(5).all()

async def resolver_cliente(db: Session, empresa_id: Any, dados: dict, telefone_auxiliar: str, config: dict) -> Any:
    if dados.get("sem_notificacao"):
        return None

    if dados.get("cliente_telefone"):
        tel = re.sub(r"\D", "", dados["cliente_telefone"])
        if not tel.startswith("55") and len(tel) >= 10:
            tel = "55" + tel

        lead = db.query(Lead).filter(Lead.empresa_id == empresa_id, Lead.telefone == tel).first()
        if not lead:
            lead = Lead(
                empresa_id=empresa_id,
                nome=dados.get("cliente_nome") or "Cliente Novo",
                telefone=tel,
                stage="agendado"
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
        return str(lead.id)

    nome_cliente = dados.get("cliente_nome")
    if not nome_cliente:
        return "aguardando_telefone"

    leads = buscar_lead_por_nome(db, empresa_id, nome_cliente)
    if len(leads) == 1:
        return str(leads[0].id)
    elif len(leads) > 1:
        from app.whatsapp import enviar_whatsapp
        opcoes = []
        for idx, l in enumerate(leads, 1):
            opcoes.append(f"{idx}. {l.nome} ({l.telefone})")
        msg = f"Encontrei {len(leads)} clientes com esse nome:\n\n" + "\n".join(opcoes) + "\n\nQual delas? Responda o número da opção (ex: 1)"

        from app.estado_auxiliar import salvar_estado_auxiliar
        salvar_estado_auxiliar(db, empresa_id, {
            "aguardando": "selecao_cliente",
            "dados_parciais": dados,
            "leads_encontrados": [str(l.id) for l in leads]
        })

        instance_name = config.get("evolution_instance") or config.get("nome_slug")
        enviar_whatsapp(instance_name, telefone_auxiliar, msg)
        return "aguardando_telefone"
    else:
        from app.whatsapp import enviar_whatsapp
        msg = f"Não encontrei {nome_cliente} nos meus contatos.\nQual o telefone dela para eu mandar a confirmação?"

        from app.estado_auxiliar import salvar_estado_auxiliar
        salvar_estado_auxiliar(db, empresa_id, {
            "aguardando": "telefone_cliente",
            "dados_parciais": dados
        })

        instance_name = config.get("evolution_instance") or config.get("nome_slug")
        enviar_whatsapp(instance_name, telefone_auxiliar, msg)
        return "aguardando_telefone"

def calcular_hora_fim(hora_inicio: str, duracao: int) -> str:
    from app.agenda_service import hm_to_min, min_to_hm
    t_start = hm_to_min(hora_inicio)
    return min_to_hm(t_start + duracao)

def montar_resumo_agendamento(dados: dict, hora_fim: str) -> str:
    try:
        dt = datetime.strptime(dados["data"], "%Y-%m-%d")
        dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        dia_semana = dias[dt.weekday()]
        data_formatada = f"{dia_semana} {dt.strftime('%d/%m')}"
    except Exception:
        data_formatada = dados["data"]

    resumo = (
        f"📋 *{dados.get('servico') or 'Serviço'}*\n"
        f"👤 *Cliente:* {dados.get('cliente_nome') or 'Cliente'}\n"
        f"📅 *Data:* {data_formatada} às {dados.get('hora')}–{hora_fim}\n"
        f"📍 *Endereço:* {dados.get('endereco') or '[sem endereço]'}"
    )
    return resumo

def montar_mensagem_confirmacao_cliente(agendamento: Any, config: dict) -> str:
    nome_agente = config.get("agenda", {}).get("nome_agente", "Rosana")
    empresa_nome = config.get("nome", "Agente Go")

    try:
        dt = datetime.strptime(agendamento.data, "%Y-%m-%d")
        dias = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
        dia_semana = dias[dt.weekday()]
        data_formatada = f"{dia_semana}, {dt.strftime('%d/%m')}"
    except Exception:
        data_formatada = agendamento.data

    msg = (
        f"Olá, {agendamento.lead.nome if agendamento.lead else 'Cliente'}! 😊\n"
        f"Seu agendamento foi marcado:\n\n"
        f"📋 *{agendamento.servico_nome}*\n"
        f"📅 *Data:* {data_formatada} às {agendamento.hora_inicio}\n"
        f"📍 *Endereço:* {agendamento.endereco or '[sem endereço]'}\n\n"
        f"Qualquer dúvida é só chamar. Até lá! 🏠✨"
    )
    return msg
