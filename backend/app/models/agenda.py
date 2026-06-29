import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(Text, default="")
    duracao_min = Column(Integer, nullable=False)
    preco = Column(Float, nullable=True)
    ativo = Column(Boolean, default=True)
    cor = Column(String, default="#3b82f6")
    ordem = Column(Integer, default=0)
    tem_variacao_caracteristica = Column(Boolean, default=False)
    caracteristicas = Column(JSONB, default=list, nullable=True)
    recorrencia_sugerida_dias = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")


class Disponibilidade(Base):
    __tablename__ = "disponibilidade"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    dia_semana = Column(Integer, nullable=True)
    data_especifica = Column(String(10), nullable=True)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    intervalo_min = Column(Integer, default=30)
    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa")


class Bloqueio(Base):
    __tablename__ = "bloqueios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    data = Column(String(10), nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    motivo = Column(Text, default="")

    empresa = relationship("Empresa")


class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="SET NULL"), nullable=True)
    servico_nome = Column(String, nullable=False)
    servico_duracao = Column(Integer, nullable=False)
    data = Column(String(10), nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    status = Column(String, default="pendente")
    observacao = Column(Text, default="")
    motivo_cancelamento = Column(Text, default="")
    endereco = Column(Text, default="")
    lembrete_cliente_enviado = Column(Boolean, default=False)
    lembrete_profissional_enviado = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")
    itens = relationship("ItemAgendamento", back_populates="agendamento", cascade="all, delete-orphan")


class ItemAgendamento(Base):
    __tablename__ = "itens_agendamento"
    id = Column(Integer, primary_key=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="SET NULL"), nullable=True)
    servico_nome = Column(String, nullable=False)
    duracao_min = Column(Integer, nullable=False)
    preco = Column(Float, nullable=True)

    agendamento = relationship("Agendamento", back_populates="itens")
    servico = relationship("Servico")


class ListaEspera(Base):
    __tablename__ = "lista_espera"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    data = Column(String(10), nullable=False)
    data_flexivel = Column(Boolean, default=False)
    posicao = Column(Integer, nullable=False)
    status = Column(String, default="aguardando") # aguardando | notificado | confirmado | expirado
    notificado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")


class SerieRecorrencia(Base):
    __tablename__ = "series_recorrencia"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    intervalo_dias = Column(Integer, nullable=False)
    ultimo_agendamento = Column(String(10), nullable=False)
    proximo_sugerido = Column(String(10), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")
