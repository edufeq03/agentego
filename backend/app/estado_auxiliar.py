import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.database import EstadoAuxiliar, SessionLocal

logger = logging.getLogger(__name__)

def salvar_estado_auxiliar(db: Session, empresa_id: Any, estado: dict):
    """Salva ou atualiza o estado da conversa com o profissional (número auxiliar)."""
    try:
        est = db.query(EstadoAuxiliar).filter(EstadoAuxiliar.empresa_id == empresa_id).first()
        if not est:
            est = EstadoAuxiliar(empresa_id=empresa_id)
            db.add(est)
        est.estado_json = json.dumps(estado)
        est.atualizado_em = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar estado auxiliar para empresa={empresa_id}: {e}")
        db.rollback()

def carregar_estado_auxiliar(db: Session, empresa_id: Any) -> Optional[dict]:
    """Carrega o estado da conversa com o profissional (número auxiliar)."""
    try:
        est = db.query(EstadoAuxiliar).filter(EstadoAuxiliar.empresa_id == empresa_id).first()
        if est and est.estado_json:
            return json.loads(est.estado_json)
    except Exception as e:
        logger.error(f"Erro ao carregar estado auxiliar para empresa={empresa_id}: {e}")
    return None

def limpar_estado_auxiliar(db: Session, empresa_id: Any):
    """Remove o estado da conversa com o profissional."""
    try:
        db.query(EstadoAuxiliar).filter(EstadoAuxiliar.empresa_id == empresa_id).delete()
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao limpar estado auxiliar para empresa={empresa_id}: {e}")
        db.rollback()

def job_limpar_estados_expirados():
    """Tarefa periódica para limpar estados não atualizados nos últimos 30 minutos."""
    db = SessionLocal()
    try:
        limite = datetime.utcnow() - timedelta(minutes=30)
        deletados = db.query(EstadoAuxiliar).filter(EstadoAuxiliar.atualizado_em < limite).delete()
        db.commit()
        if deletados > 0:
            logger.info(f"Limpeza de estados expirados: {deletados} estados limpos.")
    except Exception as e:
        logger.error(f"Erro no job job_limpar_estados_expirados: {e}")
        db.rollback()
    finally:
        db.close()
