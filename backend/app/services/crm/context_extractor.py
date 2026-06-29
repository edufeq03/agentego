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
