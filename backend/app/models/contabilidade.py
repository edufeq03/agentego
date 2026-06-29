import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class EmpresaCliente(Base):
    __tablename__ = "empresas_clientes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome_empresa = Column(String, nullable=False)
    cnpj = Column(String, nullable=True)
    regime_tributario = Column(String, nullable=True)
    contato_nome = Column(String, nullable=True)
    contato_telefone = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="empresas_clientes")


class ObrigacaoFiscal(Base):
    __tablename__ = "obrigacoes_fiscais"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    empresa_cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas_clientes.id"), nullable=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    prazo = Column(DateTime, nullable=False)
    status = Column(String, default="pendente")
    aviso_enviado = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="obrigacoes_fiscais")


class DocumentoLegal(Base):
    __tablename__ = "documentos_legais"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String, nullable=False)
    categoria = Column(String, nullable=True)
    conteudo = Column(Text, nullable=False)
    fonte = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="documentos_legais")
