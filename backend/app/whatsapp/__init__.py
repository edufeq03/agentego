from .base import (
    WhatsAppProvider, 
    TipoMensagem, 
    TipoPresenca, 
    ResultadoEnvio, 
    WebhookEvent
)
from .dispatcher import WhatsAppDispatcher, get_dispatcher
import asyncio
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "WhatsAppProvider",
    "TipoMensagem",
    "TipoPresenca",
    "ResultadoEnvio",
    "WebhookEvent",
    "WhatsAppDispatcher",
    "get_dispatcher",
    "enviar_whatsapp",
    "simular_digitacao",
    "simular_gravacao_audio",
    "enviar_audio_whatsapp",
    "enviar_imagem_whatsapp"
]

def _run(coro):
    """Executa coroutine em contexto síncrono (compatibilidade com código legado)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

def _resolve_empresa_id(instance_name):
    return None

def enviar_whatsapp(numero=None, mensagem=None, instance_name=None, empresa_id=None, *args, **kwargs):
    num = numero or kwargs.get("to_number") or kwargs.get("numero")
    msg = mensagem or kwargs.get("message") or kwargs.get("mensagem")
    inst = instance_name or kwargs.get("instance_name")
    
    if not num or not msg or not inst:
        logger.error(f"FALHA NO ENVIO: Parâmetros obrigatórios ausentes. numero={num}, mensagem={msg}, instance_name={inst}")
        return

    dispatcher = get_dispatcher()
    resultado = _run(dispatcher.enviar(
        empresa_id=empresa_id or _resolve_empresa_id(inst),
        telefone=num,
        tipo=TipoMensagem.TEXTO,
        contexto="atendimento",
        texto=msg,
        instance_ref=inst
    ))
    return resultado

def simular_digitacao(numero, instance_name, empresa_id=None):
    dispatcher = get_dispatcher()
    _run(dispatcher.simular_presenca(
        empresa_id=empresa_id or _resolve_empresa_id(instance_name),
        telefone=numero,
        tipo=TipoPresenca.DIGITANDO,
        instance_ref=instance_name
    ))

def simular_gravacao_audio(numero, instance_name, empresa_id=None):
    dispatcher = get_dispatcher()
    _run(dispatcher.simular_presenca(
        empresa_id=empresa_id or _resolve_empresa_id(instance_name),
        telefone=numero,
        tipo=TipoPresenca.GRAVANDO,
        instance_ref=instance_name
    ))

def enviar_audio_whatsapp(numero, caminho_audio, instance_name, empresa_id=None):
    import base64
    try:
        with open(caminho_audio, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro ao ler áudio {caminho_audio}: {e}")
        return

    dispatcher = get_dispatcher()
    resultado = _run(dispatcher.enviar(
        empresa_id=empresa_id or _resolve_empresa_id(instance_name),
        telefone=numero,
        tipo=TipoMensagem.AUDIO,
        contexto="atendimento",
        audio_base64=audio_base64,
        instance_ref=instance_name
    ))
    return resultado

def enviar_imagem_whatsapp(numero, imagem_url_ou_base64, legenda, instance_name, empresa_id=None):
    dispatcher = get_dispatcher()
    resultado = _run(dispatcher.enviar(
        empresa_id=empresa_id or _resolve_empresa_id(instance_name),
        telefone=numero,
        tipo=TipoMensagem.IMAGEM,
        contexto="atendimento",
        imagem_url=imagem_url_ou_base64,
        legenda=legenda,
        instance_ref=instance_name
    ))
    
    class DummyResponse:
        def __init__(self, res):
            self.status_code = res.status_code if res.status_code else (200 if res.sucesso else 400)
            self.text = res.erro or "OK"
            
    return DummyResponse(resultado)
