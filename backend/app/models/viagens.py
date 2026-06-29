import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class ClienteAgenciaViagens(Base):
    """Clientes específicos do nicho Agência de Viagens.
    Criados automaticamente ao primeiro contato via WhatsApp (pushName)."""
    __tablename__ = "clientes_agencia_viagens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    canal_entrada = Column(String, default="whatsapp")  # whatsapp, manual, csv
    destinos_interesse = Column(JSONB, default=list)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="clientes_agencia_viagens")
    lead = relationship("Lead")
