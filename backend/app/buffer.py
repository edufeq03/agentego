import asyncio
import os
import logging

logger = logging.getLogger(__name__)

# Configuração de tempo de debounce (Padrão: 4 segundos)
BUFFER_SECONDS = float(os.getenv("MESSAGE_BUFFER_SECONDS", "4.0"))
MAX_MESSAGES = 8

from app.redis_client import get_redis
import json

# Estrutura em RAM (Fallback): {(empresa_id, telefone): {"mensagens": ["oi"], "task": asyncio.Task}}
_buffer_ram = {}
redis_client = get_redis()

def processar_imediatamente(empresa, telefone, callback):
    """Executa o callback com o texto combinado e limpa o buffer."""
    key = f"buffer:{empresa.id}:{telefone}"
    ram_key = (empresa.id, telefone)
    
    mensagens = []
    if redis_client:
        mensagens = redis_client.lrange(key, 0, -1)
        redis_client.delete(key)
    else:
        if ram_key in _buffer_ram:
            mensagens = _buffer_ram[ram_key]["mensagens"]
            del _buffer_ram[ram_key]

    # Cancela task em RAM se houver
    if ram_key in _buffer_ram and "task" in _buffer_ram[ram_key]:
        if not _buffer_ram[ram_key]["task"].done():
            _buffer_ram[ram_key]["task"].cancel()

    if not mensagens:
        return
    
    texto_combinado = " ".join([t.strip() for t in mensagens if t.strip()])
    if not texto_combinado:
        return
        
    logger.info(f"[{telefone}] Buffer liberado ({len(mensagens)} msgs).")
    asyncio.create_task(callback(empresa, telefone, texto_combinado))

async def _esperar_e_processar(empresa, telefone, callback):
    await asyncio.sleep(BUFFER_SECONDS)
    processar_imediatamente(empresa, telefone, callback)

def adicionar_mensagem(empresa, telefone, texto: str, callback):
    key = f"buffer:{empresa.id}:{telefone}"
    ram_key = (empresa.id, telefone)
    
    # 1. Armazena a mensagem
    count = 0
    if redis_client:
        redis_client.rpush(key, texto)
        redis_client.expire(key, 60) # TTL de segurança
        count = redis_client.llen(key)
    else:
        if ram_key not in _buffer_ram:
            _buffer_ram[ram_key] = {"mensagens": [], "task": None}
        _buffer_ram[ram_key]["mensagens"].append(texto)
        count = len(_buffer_ram[ram_key]["mensagens"])
        
    # 2. Gerencia o Timer (Task sempre fica em RAM, pois asyncio.Task não vai para o Redis)
    if ram_key not in _buffer_ram:
        _buffer_ram[ram_key] = {"task": None} # Inicializa se não existia (caso do Redis)
        
    if _buffer_ram[ram_key].get("task") and not _buffer_ram[ram_key]["task"].done():
        _buffer_ram[ram_key]["task"].cancel()
        
    if count >= MAX_MESSAGES:
        processar_imediatamente(empresa, telefone, callback)
    else:
        _buffer_ram[ram_key]["task"] = asyncio.create_task(_esperar_e_processar(empresa, telefone, callback))
