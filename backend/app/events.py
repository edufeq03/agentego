from sqlalchemy.orm import Session
from app.database import Evento
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def registrar_evento(db: Session, empresa_id: str, lead_id: str, tipo: str, metadata: dict = None):
    """
    Registra um evento no banco de dados de forma padronizada.
    Tipos sugeridos pela spec:
    - iniciou_conversa
    - perguntou_preco
    - perguntou_horario
    - perguntou_aulas
    - demonstrou_interesse
    - convite_visita_feito
    - aceitou_visita
    - recusou_visita
    - transbordo_sugerido
    - transbordo_confirmado
    - transbordo_cancelado
    """
    try:
        novo_evento = Evento(
            empresa_id=empresa_id,
            lead_id=lead_id,
            tipo=tipo,
            metadata_=metadata or {},
            timestamp=datetime.utcnow()
        )
        db.add(novo_evento)
        db.commit()
        logger.info(f"Evento registrado: {tipo} para empresa {empresa_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao registrar evento {tipo}: {e}")
