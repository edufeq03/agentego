from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class TipoMensagem(str, Enum):
    TEXTO      = "texto"
    AUDIO      = "audio"
    IMAGEM     = "imagem"
    DOCUMENTO  = "documento"
    TEMPLATE   = "template"   # exclusivo Meta Cloud API
    PRESENCA   = "presenca"   # digitando / gravando (não é mensagem real)


class TipoPresenca(str, Enum):
    DIGITANDO = "composing"
    GRAVANDO  = "recording"
    PAUSADO   = "paused"


@dataclass
class ResultadoEnvio:
    """Resultado normalizado de qualquer envio, independente do provider."""
    sucesso: bool
    provider: str                    # "evolution" | "meta"
    message_id: Optional[str] = None
    erro: Optional[str] = None
    status_code: Optional[int] = None
    payload_raw: Optional[Dict[str, Any]] = None  # resposta bruta para debug


@dataclass
class WebhookEvent:
    """
    Evento de webhook normalizado.
    Qualquer provider produz este objeto — o pipeline nunca vê o payload bruto.
    """
    provider: str                    # "evolution" | "meta"
    tipo: str                        # "message" | "status_update" | "connection_update"
    empresa_id: Optional[str]        # resolvido pelo Dispatcher a partir do token/instance
    telefone_remetente: str
    mensagem_id: str
    timestamp: int                   # unix timestamp

    # Conteúdo (apenas um será preenchido por evento)
    texto: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    imagem_base64: Optional[str] = None
    imagem_url: Optional[str] = None
    documento_url: Optional[str] = None
    documento_nome: Optional[str] = None
    mimetype: Optional[str] = None
    duracao_audio_seg: Optional[int] = None

    # Metadados
    nome_remetente: Optional[str] = None
    is_group: bool = False
    quoted_message_id: Optional[str] = None
    payload_raw: Dict[str, Any] = field(default_factory=dict)  # sempre preservado para debug


class WhatsAppProvider(ABC):
    """
    Interface que todo provider deve implementar.
    O Dispatcher usa apenas estes métodos — nunca chama Evolution ou Meta diretamente.
    """

    @abstractmethod
    async def enviar_texto(
        self,
        telefone: str,
        mensagem: str,
        instance_ref: str           # evolution_instance ou meta_phone_number_id
    ) -> ResultadoEnvio:
        pass

    @abstractmethod
    async def enviar_audio(
        self,
        telefone: str,
        audio_base64: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        pass

    @abstractmethod
    async def enviar_imagem(
        self,
        telefone: str,
        imagem_url_ou_base64: str,
        legenda: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        pass

    @abstractmethod
    async def enviar_documento(
        self,
        telefone: str,
        documento_url: str,
        nome_arquivo: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        pass

    @abstractmethod
    async def enviar_template(
        self,
        telefone: str,
        template_name: str,
        params: List[str],
        instance_ref: str
    ) -> ResultadoEnvio:
        """
        Evolution não suporta templates oficiais.
        EvolutionProvider deve levantar NotImplementedError.
        """
        pass

    @abstractmethod
    async def simular_presenca(
        self,
        telefone: str,
        tipo: TipoPresenca,
        duracao_ms: int,
        instance_ref: str
    ) -> None:
        pass

    @abstractmethod
    async def processar_webhook(
        self,
        payload: Dict[str, Any],
        empresa_id: str
    ) -> Optional[WebhookEvent]:
        """
        Recebe o payload bruto do provider e retorna um WebhookEvent normalizado.
        Retorna None se o evento deve ser ignorado (ex: echo de mensagem própria).
        """
        pass

    @abstractmethod
    def criar_instancia(self, instance_name: str) -> bool:
        """Cria instância no provider (só faz sentido para Evolution)."""
        pass

    @abstractmethod
    def status_conexao(self, instance_ref: str) -> str:
        """Retorna: connected | disconnected | connecting | not_found | loading"""
        pass

    @abstractmethod
    def get_qrcode(self, instance_ref: str) -> Optional[str]:
        """Retorna base64 do QR Code (só Evolution). Meta retorna None."""
        pass

    @abstractmethod
    def configurar_webhook(self, instance_ref: str, webhook_url: str) -> tuple:
        """Configura a URL de webhook do provider."""
        pass
