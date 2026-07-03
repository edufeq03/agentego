import logging
from typing import Optional, Dict, Any, List

from .base import (
    WhatsAppProvider,
    ResultadoEnvio,
    WebhookEvent,
    TipoPresenca
)

logger = logging.getLogger(__name__)

class MetaCloudProvider(WhatsAppProvider):
    """
    Stub para a implementação futura da Meta Cloud API.
    A Meta Cloud API exige integrações diferentes como a de storage para áudio (S3),
    e o uso de Templates pré-aprovados pela Meta.
    """
    
    async def enviar_texto(
        self,
        telefone: str,
        mensagem: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    async def enviar_audio(
        self,
        telefone: str,
        audio_base64: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError(
            "Meta requer URL pública para áudio. "
            "Implementar após integração com storage S3."
        )

    async def enviar_imagem(
        self,
        telefone: str,
        imagem_url_ou_base64: str,
        legenda: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    async def enviar_documento(
        self,
        telefone: str,
        documento_url: str,
        nome_arquivo: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    async def enviar_template(
        self,
        telefone: str,
        template_name: str,
        params: List[str],
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    async def simular_presenca(
        self,
        telefone: str,
        tipo: TipoPresenca,
        duracao_ms: int,
        instance_ref: str
    ) -> None:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    async def processar_webhook(
        self,
        payload: Dict[str, Any],
        empresa_id: str
    ) -> Optional[WebhookEvent]:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")

    def criar_instancia(self, instance_name: str) -> bool:
        # Meta não usa instâncias criadas pela API localmente da mesma forma. 
        # O número é configurado no painel do Meta Business.
        return True

    def status_conexao(self, instance_ref: str) -> str:
        # Se for configurado via WABA, a conexão é dada como permanente, a não ser que revogado
        return "connected"

    def get_qrcode(self, instance_ref: str) -> Optional[str]:
        # Meta não usa QR Code para pareamento
        return None

    def configurar_webhook(self, instance_ref: str, webhook_url: str) -> tuple:
        raise NotImplementedError("Meta Cloud Provider não implementado ainda.")
