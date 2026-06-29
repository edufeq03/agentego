import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class CrmContact(Base):
    __tablename__ = "crm_contacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    source = Column(String(100), default="whatsapp") # whatsapp, manual, web_form, import
    status = Column(String(50), default="active")
    
    custom_fields = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa")
    organizations = relationship("CrmContactOrganization", back_populates="contact", cascade="all, delete-orphan")
    deals = relationship("CrmDeal", back_populates="contact")
    activities = relationship("CrmActivity", back_populates="contact")
    contexts = relationship("CrmContext", back_populates="contact", cascade="all, delete-orphan")


class CrmOrganization(Base):
    __tablename__ = "crm_organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    
    custom_fields = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa")
    contacts = relationship("CrmContactOrganization", back_populates="organization", cascade="all, delete-orphan")
    deals = relationship("CrmDeal", back_populates="organization")


class CrmContactOrganization(Base):
    __tablename__ = "crm_contact_organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("crm_organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(100), nullable=True) # Cargo / Relacionamento
    
    contact = relationship("CrmContact", back_populates="organizations")
    organization = relationship("CrmOrganization", back_populates="contacts")


class CrmPipeline(Base):
    __tablename__ = "crm_pipelines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # A estrutura dos estágios pode ser simples com JSONB ou uma tabela separada. 
    # Optamos por JSONB para maior flexibilidade e menor complexidade de queries
    # Ex: [{"id": "stage_1", "name": "Lead", "order": 1}, ...]
    stages = Column(JSONB, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa")
    deals = relationship("CrmDeal", back_populates="pipeline")


class CrmDeal(Base):
    __tablename__ = "crm_deals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("crm_pipelines.id", ondelete="RESTRICT"), nullable=False)
    stage_id = Column(String(50), nullable=False) # ID do estágio contido no pipeline.stages
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("crm_organizations.id", ondelete="SET NULL"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True) # Responsável
    
    title = Column(String(255), nullable=False)
    value = Column(Float, default=0.0)
    currency = Column(String(3), default="BRL")
    
    status = Column(String(20), default="open") # open, won, lost
    lost_reason = Column(Text, nullable=True)
    expected_close_date = Column(DateTime, nullable=True)
    
    custom_fields = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa")
    pipeline = relationship("CrmPipeline", back_populates="deals")
    contact = relationship("CrmContact", back_populates="deals")
    organization = relationship("CrmOrganization", back_populates="deals")
    owner = relationship("Usuario")
    activities = relationship("CrmActivity", back_populates="deal")


class CrmActivity(Base):
    __tablename__ = "crm_activities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    type = Column(String(50), nullable=False) # call, meeting, task, email, whatsapp
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    due_date = Column(DateTime, nullable=True)
    done = Column(Boolean, default=False)
    done_at = Column(DateTime, nullable=True)
    
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm_deals.id", ondelete="CASCADE"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id", ondelete="CASCADE"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa")
    deal = relationship("CrmDeal", back_populates="activities")
    contact = relationship("CrmContact", back_populates="activities")
    owner = relationship("Usuario")


class CrmContext(Base):
    """
    Memória estruturada da IA para um contato ou negócio.
    Usada para armazenar resumos, intenções extraídas e histórico de forma consolidada.
    """
    __tablename__ = "crm_contexts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id", ondelete="CASCADE"), nullable=True)
    
    # Contexto extraído pela IA
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)
    tags = Column(JSONB, default=list)
    key_points = Column(JSONB, default=list)
    
    last_analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa")
    contact = relationship("CrmContact", back_populates="contexts")


class CrmAuditLog(Base):
    __tablename__ = "crm_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    
    entity_type = Column(String(50), nullable=False) # deal, contact, organization, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False) # create, update, delete, stage_change
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    changes = Column(JSONB, default=dict) # {"field": {"old": "A", "new": "B"}}
    
    created_at = Column(DateTime, default=datetime.utcnow)
