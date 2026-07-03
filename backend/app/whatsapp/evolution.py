import os
import requests
import logging
import asyncio
import base64
from typing import Optional, Dict, Any, List

from .base import (
    WhatsAppProvider,
    ResultadoEnvio,
    WebhookEvent,
    TipoPresenca,
    TipoMensagem
)
from app.whatsapp_service import get_evolution_base_url, get_headers

logger = logging.getLogger(__name__)

class EvolutionProvider(WhatsAppProvider):
    
    def _run_async(self, func, *args, **kwargs):
        """Helper para rodar requests blockantes de forma síncrona/assíncrona simulada, se precisar, mas o ideal é aiohttp. Usando requests para manter a lógica original."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em requisição Evolution: {e}")
            raise

    async def enviar_texto(
        self,
        telefone: str,
        mensagem: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        base_url = get_evolution_base_url()
        url = f"{base_url}/message/sendText/{instance_ref}"
        
        payload = {
            "number": telefone,
            "text": mensagem
        }
        
        headers = {
            "apikey": os.getenv("EVOLUTION_API_KEY")
        }

        try:
            # Em refatorações futuras, substituir por aiohttp. Por hora, mantemos requests sync
            # dentro de um wrapper async para compatibilidade.
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=payload, headers=headers, timeout=15)
            )
            
            sucesso = response.status_code in [200, 201]
            if sucesso:
                logger.info(f"[{telefone}] Mensagem de texto despachada (Instância: {instance_ref}).")
            else:
                logger.error(f"[{telefone}] FALHA NO ENVIO (Status {response.status_code}): {response.text}")
                
            return ResultadoEnvio(
                sucesso=sucesso,
                provider="evolution",
                status_code=response.status_code,
                erro=response.text if not sucesso else None,
                payload_raw=response.json() if response.text else None
            )
        except Exception as e:
            logger.error(f"Exceção ao enviar texto para {telefone}: {e}")
            return ResultadoEnvio(sucesso=False, provider="evolution", erro=str(e))

    async def enviar_audio(
        self,
        telefone: str,
        audio_base64: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        base_url = get_evolution_base_url()
        url = f"{base_url}/message/sendWhatsAppAudio/{instance_ref}"
            
        payload = {
            "number": telefone,
            "audio": audio_base64,
            "options": {
                "delay": 1200,
                "presence": "recording",
                "encoding": True
            }
        }

        headers = {
            "apikey": os.getenv("EVOLUTION_API_KEY"),
            "Content-Type": "application/json"
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=payload, headers=headers, timeout=30)
            )
            
            sucesso = response.status_code in [200, 201]
            if sucesso:
                logger.info(f"[{telefone}] Áudio despachado (Instância: {instance_ref}).")
            else:
                logger.error(f"[{telefone}] FALHA NO ENVIO DO ÁUDIO (Status {response.status_code}): {response.text}")
                
            return ResultadoEnvio(
                sucesso=sucesso,
                provider="evolution",
                status_code=response.status_code,
                erro=response.text if not sucesso else None,
                payload_raw=response.json() if response.text else None
            )
        except Exception as e:
            logger.error(f"Exceção ao enviar áudio para {telefone}: {e}")
            return ResultadoEnvio(sucesso=False, provider="evolution", erro=str(e))

    async def enviar_imagem(
        self,
        telefone: str,
        imagem_url_ou_base64: str,
        legenda: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        base_url = get_evolution_base_url()
        url = f"{base_url}/message/sendMedia/{instance_ref}"
        
        payload = {
            "number": telefone,
            "mediatype": "image",
            "mimetype": "image/jpeg",
            "caption": legenda,
            "media": imagem_url_ou_base64
        }
        
        headers = {
            "apikey": os.getenv("EVOLUTION_API_KEY")
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=payload, headers=headers, timeout=20)
            )
            
            sucesso = response.status_code in [200, 201]
            if sucesso:
                logger.info(f"[{telefone}] Imagem despachada (Instância: {instance_ref}).")
            else:
                logger.error(f"[{telefone}] Erro ao enviar imagem: {response.text}")
                
            return ResultadoEnvio(
                sucesso=sucesso,
                provider="evolution",
                status_code=response.status_code,
                erro=response.text if not sucesso else None,
                payload_raw=response.json() if response.text else None
            )
        except Exception as e:
            logger.error(f"Exceção ao enviar imagem para {telefone}: {e}")
            return ResultadoEnvio(sucesso=False, provider="evolution", erro=str(e))

    async def enviar_documento(
        self,
        telefone: str,
        documento_url: str,
        nome_arquivo: str,
        instance_ref: str
    ) -> ResultadoEnvio:
        base_url = get_evolution_base_url()
        url = f"{base_url}/message/sendMedia/{instance_ref}"
        
        # Na evolution v1/v2, documento envia parecido com imagem, só muda o mediatype e adiciona fileName
        payload = {
            "number": telefone,
            "mediatype": "document",
            "fileName": nome_arquivo,
            "media": documento_url
        }
        
        headers = {
            "apikey": os.getenv("EVOLUTION_API_KEY")
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=payload, headers=headers, timeout=20)
            )
            
            sucesso = response.status_code in [200, 201]
            return ResultadoEnvio(
                sucesso=sucesso,
                provider="evolution",
                status_code=response.status_code,
                erro=response.text if not sucesso else None,
                payload_raw=response.json() if response.text else None
            )
        except Exception as e:
            return ResultadoEnvio(sucesso=False, provider="evolution", erro=str(e))

    async def enviar_template(
        self,
        telefone: str,
        template_name: str,
        params: List[str],
        instance_ref: str
    ) -> ResultadoEnvio:
        raise NotImplementedError("Evolution não suporta templates oficiais da Meta.")

    async def simular_presenca(
        self,
        telefone: str,
        tipo: TipoPresenca,
        duracao_ms: int,
        instance_ref: str
    ) -> None:
        base_url = get_evolution_base_url()
        url = f"{base_url}/chat/sendPresence/{instance_ref}"
        
        payload = {
            "number": telefone,
            "delay": duracao_ms,
            "presence": tipo.value
        }
        
        headers = {
            "apikey": os.getenv("EVOLUTION_API_KEY"),
            "Content-Type": "application/json"
        }
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=payload, headers=headers, timeout=5)
            )
        except Exception as e:
            logger.warning(f"Erro ao simular presença (não crítico): {e}")

    async def processar_webhook(
        self,
        payload: Dict[str, Any],
        empresa_id: str
    ) -> Optional[WebhookEvent]:
        
        # Ignorar eventos que não sejam de upsert de mensagem
        event_type = payload.get("event")
        if event_type != "messages.upsert":
            return None
            
        data = payload.get("data", {})
        key = data.get("key", {})
        
        # Ignorar mensagens enviadas pelo próprio bot (echo)
        if key.get("fromMe") is True:
            return None
            
        remote_jid = key.get("remoteJid", "")
        # Ignorar mensagens de grupo
        if remote_jid.endswith("@g.us"):
            return None
            
        telefone_remetente = remote_jid.replace("@s.whatsapp.net", "")
        mensagem_id = key.get("id", "")
        timestamp = data.get("messageTimestamp", 0)
        
        message_data = data.get("message", {})
        
        # Caso message venha envelopado em 'ephemeralMessage'
        if "ephemeralMessage" in message_data:
            message_data = message_data["ephemeralMessage"].get("message", {})
            
        # Determinar o tipo e extrair conteúdo
        texto = None
        audio_base64 = None
        audio_url = None
        imagem_base64 = None
        imagem_url = None
        documento_url = None
        documento_nome = None
        mimetype = None
        duracao_audio = None
        tipo_msg = "unknown"
        
        if "conversation" in message_data:
            tipo_msg = "message"
            texto = message_data["conversation"]
        elif "extendedTextMessage" in message_data:
            tipo_msg = "message"
            texto = message_data["extendedTextMessage"].get("text", "")
        elif "audioMessage" in message_data:
            tipo_msg = "audio"
            audio_info = message_data["audioMessage"]
            mimetype = audio_info.get("mimetype")
            duracao_audio = audio_info.get("seconds")
            # A base64 normalmente precisa ser solicitada para a evolution via rota separada,
            # ou depende do "webhookBase64": true
            if "base64" in payload:
                audio_base64 = payload["base64"]
            
        elif "imageMessage" in message_data:
            tipo_msg = "image"
            img_info = message_data["imageMessage"]
            mimetype = img_info.get("mimetype")
            texto = img_info.get("caption", "")
            if "base64" in payload:
                imagem_base64 = payload["base64"]
                
        elif "documentMessage" in message_data:
            tipo_msg = "document"
            doc_info = message_data["documentMessage"]
            documento_nome = doc_info.get("fileName")
            mimetype = doc_info.get("mimetype")

        # Se não soubermos o tipo, não criamos o webhook event
        if tipo_msg == "unknown":
            return None
            
        return WebhookEvent(
            provider="evolution",
            tipo=tipo_msg,
            empresa_id=empresa_id,
            telefone_remetente=telefone_remetente,
            mensagem_id=mensagem_id,
            timestamp=timestamp,
            texto=texto,
            audio_base64=audio_base64,
            audio_url=audio_url,
            imagem_base64=imagem_base64,
            imagem_url=imagem_url,
            documento_url=documento_url,
            documento_nome=documento_nome,
            mimetype=mimetype,
            duracao_audio_seg=duracao_audio,
            nome_remetente=data.get("pushName"),
            is_group=False,
            payload_raw=payload
        )

    def criar_instancia(self, instance_name: str) -> bool:
        base_url = get_evolution_base_url()
        url = f"{base_url}/instance/create"
        
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        try:
            response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Instância {instance_name} criada com sucesso (Evolution).")
                return True
            logger.error(f"Erro ao criar instância {instance_name}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Falha na requisição de criação de instância: {e}")
            return False

    def status_conexao(self, instance_ref: str) -> str:
        base_url = get_evolution_base_url()
        url = f"{base_url}/instance/connectionState/{instance_ref}"
        
        try:
            response = requests.get(url, headers=get_headers(), timeout=5)
            if response.status_code == 200:
                state = response.json().get("instance", {}).get("state", "disconnected")
                if state == "open": return "connected"
                if state == "close": return "disconnected"
                return state
            if response.status_code == 404:
                return "not_found"
            return "disconnected"
        except Exception as e:
            logger.error(f"Erro ao buscar status da instância {instance_ref}: {e}")
            return "loading"

    def get_qrcode(self, instance_ref: str) -> Optional[str]:
        base_url = get_evolution_base_url()
        url = f"{base_url}/instance/connect/{instance_ref}"
        
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("base64") or data.get("code")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar QR Code para {instance_ref}: {e}")
            return None

    def configurar_webhook(self, instance_ref: str, webhook_url: str) -> tuple:
        base_url = get_evolution_base_url()
        url = f"{base_url}/webhook/set/{instance_ref}"
        
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "webhookByEvents": False,
                "byEvents": False,
                "webhookBase64": True,
                "base64": True,
                "events": [
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "MESSAGES_DELETE",
                    "SEND_MESSAGE",
                    "CONNECTION_UPDATE",
                    "CALL",
                    "TYPEBOT_START",
                    "TYPEBOT_CHANGE_STATUS"
                ]
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                return True, None
            return False, f"Evolution Status {response.status_code}: {response.text}"
        except Exception as e:
            logger.error(f"Erro ao configurar webhook para {instance_ref}: {e}")
            return False, str(e)
