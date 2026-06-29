import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class Campanha(Base):
    __tablename__ = "campanhas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    codigo_ref = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    origem = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="campanhas")


class Comunicado(Base):
    __tablename__ = "comunicados"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    mensagem = Column(Text, nullable=False)
    imagem_url = Column(Text, nullable=True)
    data_programada = Column(DateTime, nullable=True)
    status = Column(String, default="pendente") # rascunho, pendente, enviando, enviado, erro
    total_membros = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    enviado_em = Column(DateTime, nullable=True)

    empresa = relationship("Empresa")


class ComunicadoLog(Base):
    __tablename__ = "comunicado_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comunicado_id = Column(UUID(as_uuid=True), ForeignKey("comunicados.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    status = Column(String, nullable=False) # sucesso, erro
    erro = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    comunicado = relationship("Comunicado")


class ListaTransmissao(Base):
    __tablename__ = "listas_transmissao"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="listas_transmissao")
    contatos = relationship("ListaTransmissaoContato", back_populates="lista", cascade="all, delete-orphan")
    disparos = relationship("DisparoLista", back_populates="lista", cascade="all, delete-orphan")


class ListaTransmissaoContato(Base):
    __tablename__ = "listas_transmissao_contatos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lista_id = Column(UUID(as_uuid=True), ForeignKey("listas_transmissao.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=True)
    telefone = Column(String, nullable=False)
    adicionado_em = Column(DateTime, default=datetime.utcnow)

    lista = relationship("ListaTransmissao", back_populates="contatos")


class DisparoLista(Base):
    __tablename__ = "disparos_lista"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lista_id = Column(UUID(as_uuid=True), ForeignKey("listas_transmissao.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    mensagem = Column(Text, nullable=False)
    imagem_url = Column(Text, nullable=True)
    status = Column(String, default="pendente")  # pendente, enviando, enviado, erro
    total_contatos = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    data_programada = Column(DateTime, nullable=True)
    enviado_em = Column(DateTime, nullable=True)

    lista = relationship("ListaTransmissao", back_populates="disparos")
