import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class Cardapio(Base):
    __tablename__ = "cardapio"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    categoria = Column(String, nullable=False) # Lanches, Bebidas, Sobremesas, etc.
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    disponivel = Column(Boolean, default=True)
    ordem = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")


class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    numero_pedido = Column(Integer, primary_key=False, nullable=True) # Sequencial por empresa ou autoincremento
    modo = Column(String, nullable=False) # 'delivery', 'balcao', 'mesa'
    status = Column(String, default="aguardando") # aguardando, em_preparo, pronto, entregue, cancelado
    total = Column(Float, nullable=True)
    observacao = Column(Text, nullable=True)
    endereco = Column(Text, nullable=True)
    nome_balcao = Column(String, nullable=True)
    numero_mesa = Column(Integer, nullable=True)
    avaliacao_nota = Column(Integer, nullable=True)
    avaliacao_comentario = Column(Text, nullable=True)
    pagamento_status = Column(String, default="pendente") # pendente, pago
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class FollowupDelivery(Base):
    __tablename__ = "followup_delivery"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    agendado_para = Column(DateTime, nullable=False)
    status = Column(String, default="pendente") # pendente, enviado, avaliado
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    pedido = relationship("Pedido")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    cardapio_id = Column(UUID(as_uuid=True), ForeignKey("cardapio.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String, nullable=False)
    preco_unit = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)
    observacao = Column(Text, nullable=True)

    pedido = relationship("Pedido", back_populates="itens")
    cardapio = relationship("Cardapio")
