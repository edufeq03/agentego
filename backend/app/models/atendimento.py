import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    stage = Column(String, default='novo') # novo, curioso, interessado, quente, agendado, perdido
    visit_offer_made = Column(Boolean, default=False)
    utm_source = Column(String(50), nullable=True)
    utm_campaign = Column(String(50), nullable=True)
    canal_entrada = Column(String(50), default='organico')
    dados_customizados = Column(JSONB, nullable=False, default=dict)
    
    # Integração com o CRM
    crm_contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id", ondelete="SET NULL"), nullable=True)
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="leads")
    mensagens = relationship("Mensagem", back_populates="lead", cascade="all, delete-orphan")
    seguro = relationship("LeadSeguro", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    crm_contact = relationship("CrmContact")


class Mensagem(Base):
    __tablename__ = "mensagens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    tipo = Column(String, nullable=False) # 'usuario' ou 'agente'
    mensagem = Column(Text, nullable=False)
    intencao = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="mensagens")
    empresa = relationship("Empresa", back_populates="mensagens")


class Evento(Base):
    __tablename__ = "eventos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    tipo = Column(String, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict) # 'metadata' é reservado em sqlalchemy
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="eventos")
    lead = relationship("Lead")


class Transbordo(Base):
    __tablename__ = "transbordo"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    status = Column(String, default="aguardando") # aguardando, pausado
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="transbordos")


class EstadoAuxiliar(Base):
    __tablename__ = "estado_auxiliar"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    estado_json = Column(Text, nullable=False, default="{}")
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")


class CampoCustomizado(Base):
    __tablename__ = "campos_customizados"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    chave = Column(String(50), nullable=False)
    label = Column(String(100), nullable=False)
    tipo = Column(String(30), default="texto") # texto, numero, booleano, opcao_unica
    obrigatorio = Column(Boolean, default=False)
    opcoes = Column(JSONB, nullable=True) # Ex: ["particular", "trabalho"]
    ordem = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    dependencias = Column(JSONB, nullable=True) # Ex: {"tipo_seguro": ["Carro", "Moto"]}
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
