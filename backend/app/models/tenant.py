import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    telefone_whatsapp = Column(String, unique=True, nullable=False)
    telefone_proprietario = Column(String, nullable=True)
    webhook_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    evolution_instance = Column(String, unique=True, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    valor_mensalidade = Column(Float, default=0.0)
    data_expiracao_teste = Column(DateTime, nullable=True)
    cupom_vendedor = Column(String, nullable=True)
    
    # Billing e Planos
    plano = Column(String, default="trial") # trial, starter, pro, ilimitado
    limite_conversas_mes = Column(Integer, default=100)
    conversas_mes_atual = Column(Integer, default=0)
    data_reset_contador = Column(DateTime, nullable=True)
    
    # Rastreamento interno de custos (tokens)
    tokens_input_mes = Column(Integer, default=0)
    tokens_output_mes = Column(Integer, default=0)
    
    data_criacao = Column(DateTime, server_default=func.now())
    etapas_funil = Column(JSONB, default=["novo", "curioso", "interessado", "agendado"])
    nicho = Column(String, default="generico")
    
    # Relacionamentos
    configuracoes = relationship("Configuracao", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="empresa", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    mensagens = relationship("Mensagem", back_populates="empresa", cascade="all, delete-orphan")
    eventos = relationship("Evento", back_populates="empresa", cascade="all, delete-orphan")
    transbordos = relationship("Transbordo", back_populates="empresa", cascade="all, delete-orphan")
    campanhas = relationship("Campanha", back_populates="empresa", cascade="all, delete-orphan")
    membros_academia = relationship("MembroAcademia", back_populates="empresa", cascade="all, delete-orphan")
    empresas_clientes = relationship("EmpresaCliente", back_populates="empresa", cascade="all, delete-orphan")
    obrigacoes_fiscais = relationship("ObrigacaoFiscal", back_populates="empresa", cascade="all, delete-orphan")
    documentos_legais = relationship("DocumentoLegal", back_populates="empresa", cascade="all, delete-orphan")
    comunicados = relationship("Comunicado", back_populates="empresa", cascade="all, delete-orphan")
    leads_seguro = relationship("LeadSeguro", back_populates="empresa", cascade="all, delete-orphan")
    clientes_agencia_viagens = relationship("ClienteAgenciaViagens", back_populates="empresa", cascade="all, delete-orphan")
    listas_transmissao = relationship("ListaTransmissao", back_populates="empresa", cascade="all, delete-orphan")


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    role = Column(String, default="client") # "client" ou "admin" (franqueador)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="usuarios")


class CodigoRecuperacao(Base):
    __tablename__ = "codigos_recuperacao"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    codigo = Column(String, nullable=False)
    expira_em = Column(DateTime, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    usuario = relationship("Usuario")


class Configuracao(Base):
    __tablename__ = "configuracoes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True)
    config = Column(JSONB, nullable=False, default=dict)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="configuracoes")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_nicho = Column(String, unique=True, nullable=False)
    prompt_sistema = Column(Text, nullable=False)
    tom_voz = Column(Text, nullable=True)
    missao = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    etapas_funil = Column(JSONB, default=["novo", "curioso", "interessado", "agendado"])
    nicho = Column(String, default="generico")
    criado_em = Column(DateTime, default=datetime.utcnow)
