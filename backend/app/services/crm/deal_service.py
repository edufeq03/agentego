from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID
from fastapi import HTTPException

from app.models.crm import CrmDeal, CrmPipeline
from app.schemas.crm import CrmDealCreate

def create_deal(db: Session, empresa_id: UUID, deal_in: CrmDealCreate) -> CrmDeal:
    # Validate Pipeline
    pipeline = db.query(CrmPipeline).filter(CrmPipeline.id == deal_in.pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    db_deal = CrmDeal(
        empresa_id=empresa_id,
        **deal_in.model_dump()
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def get_deal(db: Session, deal_id: UUID) -> Optional[CrmDeal]:
    return db.query(CrmDeal).filter(CrmDeal.id == deal_id).first()

def get_deals_by_empresa(db: Session, empresa_id: UUID, skip: int = 0, limit: int = 100) -> List[Any]:
    from app.models.atendimento import Lead, Mensagem
    
    deals = db.query(CrmDeal).filter(CrmDeal.empresa_id == empresa_id).offset(skip).limit(limit).all()
    
    for deal in deals:
        deal.phone = None
        deal.intent = None
        deal.summary = None
        
        if deal.contact_id:
            if deal.contact:
                deal.phone = deal.contact.phone
                
            lead = db.query(Lead).filter(Lead.crm_contact_id == deal.contact_id).first()
            if lead:
                # Tenta pegar a intenção da última mensagem do usuário
                last_msg = db.query(Mensagem).filter(
                    Mensagem.lead_id == lead.id,
                    Mensagem.tipo == "usuario"
                ).order_by(Mensagem.timestamp.desc()).first()
                
                if last_msg and getattr(last_msg, 'intencao', None):
                    deal.intent = last_msg.intencao
                else:
                    # Fallback para o stage do lead
                    deal.intent = lead.stage.capitalize() if lead.stage else None
                    
                # Formata os dados capturados como um resumo curto
                dados = lead.dados_customizados or {}
                if dados:
                    parts = []
                    for k, v in dados.items():
                        if isinstance(v, (str, int, float, bool)) and len(str(v)) < 50:
                            parts.append(f"{k.replace('_', ' ').capitalize()}: {v}")
                    if parts:
                        deal.summary = " | ".join(parts)
                    elif "resumo_ia" in dados:
                        deal.summary = dados["resumo_ia"]
                
                if not deal.summary:
                    deal.summary = "Nenhum dado capturado durante a triagem."
                    
    return deals

def move_deal_stage(db: Session, deal_id: UUID, new_stage_id: str) -> Optional[CrmDeal]:
    deal = get_deal(db, deal_id)
    if not deal:
        return None
        
    deal.stage_id = new_stage_id
    db.commit()
    db.refresh(deal)
    return deal

def convert_lead_to_deal(db: Session, empresa_id: UUID, lead_id: UUID) -> CrmDeal:
    from app.models.atendimento import Lead
    from app.models.crm import CrmContact
    
    # 1. Obter o lead
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.empresa_id == empresa_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    # 2. Obter ou Criar o CrmContact
    contact_id = lead.crm_contact_id
    if not contact_id:
        nome_completo = lead.nome or "Desconhecido"
        partes_nome = nome_completo.split(" ", 1)
        first_name = partes_nome[0]
        last_name = partes_nome[1] if len(partes_nome) > 1 else ""

        new_contact = CrmContact(
            empresa_id=empresa_id,
            first_name=first_name,
            last_name=last_name,
            phone=lead.telefone,
            source="whatsapp",
            status="lead"
        )
        db.add(new_contact)
        db.flush() # Para pegar o ID gerado
        
        lead.crm_contact_id = new_contact.id
        contact_id = new_contact.id
    
    # 3. Obter o Pipeline Padrão
    pipeline = db.query(CrmPipeline).filter(
        CrmPipeline.empresa_id == empresa_id, 
        CrmPipeline.is_default == True
    ).first()
    
    if not pipeline:
        pipeline = db.query(CrmPipeline).filter(CrmPipeline.empresa_id == empresa_id).first()
        
    if not pipeline:
        raise HTTPException(status_code=400, detail="Nenhum pipeline configurado no CRM.")
    
    # 4. Obter a primeira etapa do pipeline
    if not pipeline.stages or len(pipeline.stages) == 0:
        raise HTTPException(status_code=400, detail="Pipeline não possui etapas configuradas.")
        
    first_stage_id = pipeline.stages[0]["id"]

    # 5. Criar a oportunidade (Deal)
    deal_title = f"Oportunidade - {lead.nome or lead.telefone}"
    
    db_deal = CrmDeal(
        empresa_id=empresa_id,
        pipeline_id=pipeline.id,
        stage_id=first_stage_id,
        contact_id=contact_id,
        title=deal_title,
        value=0.0,
        currency="BRL",
        status="open"
    )
    
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    
    return db_deal
