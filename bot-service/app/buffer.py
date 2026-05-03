import asyncio
import os
import logging

logger = logging.getLogger(__name__)

# Configuração de tempo de debounce (Padrão: 4 segundos)
BUFFER_SECONDS = float(os.getenv("MESSAGE_BUFFER_SECONDS", "4.0"))
MAX_MESSAGES = 8

# Estrutura: {(empresa_id, telefone): {"mensagens": ["oi", "tudo bem?"], "task": asyncio.Task}}
_buffer = {}

def processar_imediatamente(empresa, telefone, callback):
    """Executa o callback com o texto combinado e limpa o buffer."""
    key = (empresa.id, telefone)
    if key not in _buffer:
        return
    
    textos = _buffer[key]["mensagens"]
    # Limpa o buffer
    if "task" in _buffer[key] and not _buffer[key]["task"].done():
        _buffer[key]["task"].cancel()
    del _buffer[key]
    
    # Junta as mensagens em um único bloco de texto
    texto_combinado = " ".join([t.strip() for t in textos if t.strip()])
    if not texto_combinado:
        return
        
    logger.info(f"[{telefone}] Buffer liberado ({len(textos)} msgs consolidadas). Processando pipeline...")
    # Executa a callback (que chamará o pipeline e o envio pelo whatsapp)
    asyncio.create_task(callback(empresa, telefone, texto_combinado))

async def _esperar_e_processar(empresa, telefone, callback):
    """Espera o tempo configurado. Se não for cancelado, dispara o processamento."""
    await asyncio.sleep(BUFFER_SECONDS)
    processar_imediatamente(empresa, telefone, callback)

def adicionar_mensagem(empresa, telefone, texto: str, callback):
    """
    Adiciona uma nova mensagem ao buffer do usuário.
    Reinicia o contador de tempo.
    """
    key = (empresa.id, telefone)
    
    if key not in _buffer:
        _buffer[key] = {"mensagens": [], "task": None}
        
    # Cancela a tarefa anterior, se existir e ainda estiver rodando
    if _buffer[key]["task"] and not _buffer[key]["task"].done():
        _buffer[key]["task"].cancel()
        
    _buffer[key]["mensagens"].append(texto)
    
    # Se o cliente mandou muitas mensagens seguidas, não espera mais.
    if len(_buffer[key]["mensagens"]) >= MAX_MESSAGES:
        logger.info(f"[{telefone}] Buffer atingiu limite de {MAX_MESSAGES} msgs. Processando imediatamente.")
        processar_imediatamente(empresa, telefone, callback)
    else:
        # Cria uma nova tarefa de espera
        _buffer[key]["task"] = asyncio.create_task(_esperar_e_processar(empresa, telefone, callback))
