from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.crm import CrmContext
from app.schemas.crm import CrmContextCreate

def update_contact_context(db: Session, empresa_id: UUID, contact_id: UUID, context_data: CrmContextCreate) -> CrmContext:
    """
    Atualiza ou cria a memória de contexto estruturada para um Contato.
    Usado quando o Agente LLM sumariza uma conversa extensa.
    """
    db_context = db.query(CrmContext).filter(CrmContext.contact_id == contact_id).first()
    
    if not db_context:
        db_context = CrmContext(
            empresa_id=empresa_id,
            contact_id=contact_id
        )
        db.add(db_context)
        
    if context_data.summary:
        db_context.summary = context_data.summary
    if context_data.sentiment:
        db_context.sentiment = context_data.sentiment
    if context_data.tags:
        db_context.tags = context_data.tags
    if context_data.key_points:
        db_context.key_points = context_data.key_points
        
    db_context.last_analyzed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_context)
    return db_context

import json
from fastapi import HTTPException
from app.models.atendimento import Lead, Mensagem
from app.openai_client import client

def generate_ai_summary(db: Session, empresa_id: UUID, contact_id: UUID) -> CrmContext:
    # 1. Obter o Lead associado ao contato
    lead = db.query(Lead).filter(Lead.crm_contact_id == contact_id, Lead.empresa_id == empresa_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Não há Lead do WhatsApp associado a este contato.")
        
    # 2. Obter as mensagens
    mensagens = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp).all()
    if not mensagens:
        raise HTTPException(status_code=400, detail="Não há histórico de conversas para este Lead.")
        
    historico_texto = []
    for msg in mensagens:
        remetente = "Lead" if msg.tipo == "usuario" else "Agente/Sistema"
        historico_texto.append(f"{remetente}: {msg.mensagem}")
        
    historico_formatado = "\n".join(historico_texto)
    
    # 3. Chamar OpenAI para sumarização
    system_prompt = """
    Você é um assistente especialista em CRM de Vendas.
    Sua tarefa é analisar o histórico de conversa entre um Lead (cliente em potencial) e um Agente de Vendas.
    Gere um resumo em formato JSON EXATAMENTE com a seguinte estrutura, sem nenhum texto extra ou markdown:
    {
        "summary": "Um resumo executivo focado nas necessidades do cliente, restrições e intenção de compra. Máximo 4 frases.",
        "sentiment": "Quente" ou "Morno" ou "Frio" ou "Curioso",
        "tags": ["tag1", "tag2", "tag3"],
        "key_points": ["Ponto principal 1", "Restrição 1", "Pedido específico 1"]
    }
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Histórico:\n{historico_formatado}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        texto_resposta = response.choices[0].message.content
        dados_json = json.loads(texto_resposta)
        
        context_data = CrmContextCreate(
            contact_id=contact_id,
            summary=dados_json.get("summary", ""),
            sentiment=dados_json.get("sentiment", ""),
            tags=dados_json.get("tags", []),
            key_points=dados_json.get("key_points", [])
        )
        
        return update_contact_context(db, empresa_id, contact_id, context_data)
        
    except Exception as e:
        print(f"Erro ao gerar resumo AI: {e}")
        raise HTTPException(status_code=500, detail="Falha ao se comunicar com a IA para gerar resumo.")
