import redis
import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Testa a conexão
    redis_client.ping()
    logger.info(f"Conectado ao Redis em {REDIS_URL}")
except Exception as e:
    logger.warning(f"Não foi possível conectar ao Redis ({e}). O sistema usará fallback para memória RAM.")
    redis_client = None

def get_redis():
    return redis_client
