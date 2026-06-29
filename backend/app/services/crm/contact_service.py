from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.crm import CrmContact
from app.models.atendimento import Lead
from app.schemas.crm import CrmContactCreate

def create_contact(db: Session, empresa_id: UUID, contact_in: CrmContactCreate) -> CrmContact:
    db_contact = CrmContact(
        empresa_id=empresa_id,
        **contact_in.model_dump()
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: UUID) -> Optional[CrmContact]:
    return db.query(CrmContact).filter(CrmContact.id == contact_id).first()

def get_contacts_by_empresa(db: Session, empresa_id: UUID, skip: int = 0, limit: int = 100) -> List[CrmContact]:
    return db.query(CrmContact).filter(CrmContact.empresa_id == empresa_id).offset(skip).limit(limit).all()

def convert_lead_to_contact(db: Session, lead_id: UUID) -> Optional[CrmContact]:
    """Ponte: Converte um Lead de WhatsApp em um Contato de CRM."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
        
    if lead.crm_contact_id:
        return get_contact(db, lead.crm_contact_id)
        
    contact_in = CrmContactCreate(
        first_name=lead.nome if lead.nome else "Lead Sem Nome",
        phone=lead.telefone,
        source="whatsapp_lead",
        custom_fields=lead.dados_customizados
    )
    
    new_contact = create_contact(db, lead.empresa_id, contact_in)
    
    # Atualiza o lead vinculando-o ao novo contato
    lead.crm_contact_id = new_contact.id
    db.commit()
    
    return new_contact
