import json
import random
import asyncio
import time
import logging
from typing import Optional, Dict, Any, List

from .base import WhatsAppProvider, TipoMensagem, TipoPresenca, ResultadoEnvio, WebhookEvent
from .evolution import EvolutionProvider
from .meta import MetaCloudProvider

logger = logging.getLogger(__name__)

class WhatsAppDispatcher:
    def __init__(self, redis_client=None, db_session_factory=None):
        self._providers: Dict[str, WhatsAppProvider] = {}
        self._redis = redis_client
        self._db = db_session_factory

    def _get_provider_instance(self, provider_name: str) -> WhatsAppProvider:
        if provider_name == "evolution":
            return EvolutionProvider()
        elif provider_name == "meta":
            return MetaCloudProvider()
        else:
            # Default to evolution
            return EvolutionProvider()

    async def _get_provider_config(self, empresa_id: str):
        """Retorna (provider, instance_ref, rate_config) simulando ou consultando DB."""
        # Se tivéssemos o DB diretamente, faríamos a query aqui. 
        # Como o db_session_factory pode ser yield e depender de requests, 
        # para o shim usaremos configs default ou consultaremos cache redis se disponível.
        
        provider_name = "evolution"
        # O ideal seria puxar do banco: SELECT config_whatsapp, nome_instancia FROM empresas WHERE id = empresa_id
        # Vamos assumir que configuramos via Redis cache, ou usaremos defaults
        
        # Para compatibilidade do shim que não passa empresa_id, assumimos a instância pelo instance_name
        rate_config = {
            "mensagens_por_minuto": 12,
            "delay_atendimento_ms": 1500,
            "delay_notificacao_ms": 2000,
            "delay_campanha_min_ms": 3000,
            "delay_campanha_max_ms": 6000,
            "campanha_limite_por_minuto": 8
        }
        return self._get_provider_instance(provider_name), rate_config

    async def _aplicar_rate_limit(self, empresa_id: str, contexto: str, rate_config: dict):
        if not self._redis:
            # Fallback sem rate limit real
            await asyncio.sleep(rate_config.get("delay_atendimento_ms", 1500) / 1000.0)
            return

        loop = asyncio.get_event_loop()
        
        if contexto == "atendimento":
            delay_ms = rate_config.get("delay_atendimento_ms", 1500)
            limite = rate_config.get("mensagens_por_minuto", 20)
        elif contexto == "notificacao":
            delay_ms = rate_config.get("delay_notificacao_ms", 2000)
            limite = rate_config.get("notificacao_limite_por_minuto", 10)
        elif contexto == "campanha":
            min_ms = rate_config.get("delay_campanha_min_ms", 3000)
            max_ms = rate_config.get("delay_campanha_max_ms", 6000)
            delay_ms = random.uniform(min_ms, max_ms)
            limite = rate_config.get("campanha_limite_por_minuto", 8)
        else:
            delay_ms = 1500
            limite = 20

        # Simples rate limiting usando Redis (janela deslizante ou bucket)
        key_timestamps = f"whatsapp:rate:{empresa_id}:timestamps"
        now = time.time()
        
        try:
            # Limpa timestamps antigos (mais de 60s)
            await loop.run_in_executor(None, self._redis.zremrangebyscore, key_timestamps, 0, now - 60)
            
            # Conta mensagens no último minuto
            count = await loop.run_in_executor(None, self._redis.zcard, key_timestamps)
            
            if count >= limite:
                logger.warning(f"Rate limit atingido para a empresa {empresa_id}. Atrasando envio.")
                # Em um cenário real, poderíamos colocar numa fila ou dar sleep. Para "atendimento" é ruim dar sleep muito longo.
                # Como é proteção, vamos dar um sleep adicional
                await asyncio.sleep(2.0)
                
            # Registra o timestamp atual
            await loop.run_in_executor(None, self._redis.zadd, key_timestamps, {str(now): now})
            
        except Exception as e:
            logger.warning(f"Falha ao aplicar rate limit no redis: {e}")
            
        # Aplica o delay intrínseco
        await asyncio.sleep(delay_ms / 1000.0)

    async def enviar(
        self,
        empresa_id: str,
        telefone: str,
        tipo: TipoMensagem,
        contexto: str,
        texto: str = None,
        audio_base64: str = None,
        imagem_url: str = None,
        legenda: str = None,
        documento_url: str = None,
        documento_nome: str = None,
        template_name: str = None,
        template_params: list = None,
        instance_ref: str = None # Usado para fallback caso empresa_id seja ausente
    ) -> ResultadoEnvio:
        
        provider, rate_config = await self._get_provider_config(empresa_id)
        
        if contexto != "direto": # direto pula rate limit (usado pelo shim sync antigo se precisar)
            await self._aplicar_rate_limit(empresa_id, contexto, rate_config)

        if tipo == TipoMensagem.TEXTO:
            resultado = await provider.enviar_texto(telefone, texto, instance_ref)
        elif tipo == TipoMensagem.AUDIO:
            resultado = await provider.enviar_audio(telefone, audio_base64, instance_ref)
        elif tipo == TipoMensagem.IMAGEM:
            resultado = await provider.enviar_imagem(telefone, imagem_url, legenda, instance_ref)
        elif tipo == TipoMensagem.DOCUMENTO:
            resultado = await provider.enviar_documento(telefone, documento_url, documento_nome, instance_ref)
        elif tipo == TipoMensagem.TEMPLATE:
            resultado = await provider.enviar_template(telefone, template_name, template_params or [], instance_ref)
        else:
            return ResultadoEnvio(sucesso=False, provider=provider.__class__.__name__, erro="Tipo de mensagem não suportado.")

        if empresa_id:
            await self._registrar_auditoria(empresa_id, telefone, tipo.value, contexto, resultado)
            
        return resultado

    async def _registrar_auditoria(self, empresa_id: str, telefone: str, tipo: str, contexto: str, resultado: ResultadoEnvio):
        # Aqui seria a inserção no banco de dados na tabela whatsapp_send_log.
        pass

    async def simular_presenca(
        self,
        empresa_id: str,
        telefone: str,
        tipo: TipoPresenca,
        duracao_ms: int = 2000,
        instance_ref: str = None
    ) -> None:
        provider, _ = await self._get_provider_config(empresa_id)
        await provider.simular_presenca(telefone, tipo, duracao_ms, instance_ref)

    # ── Métodos síncronos delegados para configuração de instâncias
    def criar_instancia(self, provider_name: str, instance_name: str) -> bool:
        return self._get_provider_instance(provider_name).criar_instancia(instance_name)

    def status_conexao(self, provider_name: str, instance_ref: str) -> str:
        return self._get_provider_instance(provider_name).status_conexao(instance_ref)

    def get_qrcode(self, provider_name: str, instance_ref: str) -> Optional[str]:
        return self._get_provider_instance(provider_name).get_qrcode(instance_ref)

    def configurar_webhook(self, provider_name: str, instance_ref: str, webhook_url: str) -> tuple:
        return self._get_provider_instance(provider_name).configurar_webhook(instance_ref, webhook_url)


# Singleton
_dispatcher_instance = None

def get_dispatcher() -> WhatsAppDispatcher:
    global _dispatcher_instance
    if _dispatcher_instance is None:
        from app.redis_client import get_redis
        _dispatcher_instance = WhatsAppDispatcher(redis_client=get_redis())
    return _dispatcher_instance
