import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class MembroAcademia(Base):
    __tablename__ = "membros_academia"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    plano_nome = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    aviso_7_dias_enviado = Column(Boolean, default=False)
    aviso_3_dias_enviado = Column(Boolean, default=False)
    aviso_vencido_enviado = Column(Boolean, default=False)
    importado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")
