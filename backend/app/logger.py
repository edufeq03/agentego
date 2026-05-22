import logging
import json
import datetime
import sys

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        
        # Adiciona campos extras se existirem (ex: extra={"empresa_id": "..."})
        if hasattr(record, "empresa_id"):
            log_record["empresa_id"] = record.empresa_id
        if hasattr(record, "lead_id"):
            log_record["lead_id"] = record.lead_id
        if hasattr(record, "tipo"):
            log_record["tipo"] = record.tipo
            
        # Trata exceções
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    """
    Configura o logging global para usar o formatador JSON.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    # Suprime logs excessivos de bibliotecas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger
