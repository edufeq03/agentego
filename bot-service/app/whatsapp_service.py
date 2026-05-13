import requests
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_evolution_base_url():
    """Extrai a URL base da Evolution a partir da EVOLUTION_URL configurada."""
    url = os.getenv("EVOLUTION_URL", "")
    if not url:
        return ""
    
    # Se a URL tem o sufixo de envio, remove ele
    if "/message/sendText" in url:
        base = url.split("/message/sendText")[0]
    else:
        # Se for uma URL pura, garante que não termina em barra
        base = url.rstrip("/")
        
    print(f"DEBUG WHATSAPP -> Base URL extraída: {base}")
    return base

def get_headers():
    return {
        "apikey": os.getenv("EVOLUTION_API_KEY"),
        "Content-Type": "application/json"
    }

def create_instance(instance_name: str) -> bool:
    """Cria uma nova instância na Evolution API."""
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
            logger.info(f"Instância {instance_name} criada com sucesso.")
            return True
        logger.error(f"Erro ao criar instância {instance_name}: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Falha na requisição de criação de instância: {e}")
        return False

def get_connection_status(instance_name: str) -> str:
    """Retorna o status da conexão: 'connected', 'disconnected', 'connecting' ou 'not_found'."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/instance/connectionState/{instance_name}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            state = response.json().get("instance", {}).get("state", "disconnected")
            # Mapeia 'open' (Evolution v2) para 'connected' (Nosso Dashboard)
            if state == "open":
                return "connected"
            if state == "close":
                return "disconnected"
            return state
        if response.status_code == 404:
            return "not_found"
        return "disconnected"
    except Exception as e:
        logger.error(f"Erro ao buscar status da instância {instance_name}: {e}")
        # Retorna 'loading' em caso de erro de rede temporário para evitar que a UI "pisque" como desconectado
        return "loading"

def get_qrcode(instance_name: str) -> Optional[str]:
    """Retorna o base64 do QR Code para conexão."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/instance/connect/{instance_name}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Tenta pegar de 'base64' (v2) ou 'code' (v1)
            return data.get("base64") or data.get("code")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar QR Code para {instance_name}: {e}")
        return None

def set_webhook(instance_name: str, webhook_url: str):
    """Configura o webhook para a instância."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/webhook/set/{instance_name}"
    
    payload = {
        "webhook": {
            "enabled": True,
            "url": webhook_url,
            "webhookByEvents": False,
            "webhookBase64": True,
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
        logger.error(f"Erro ao configurar webhook para {instance_name}: {e}")
        return False, str(e)

def logout_instance(instance_name: str) -> bool:
    """Desconecta o WhatsApp da instância."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/instance/logout/{instance_name}"
    
    try:
        response = requests.delete(url, headers=get_headers(), timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def update_settings(instance_name: str):
    """Configura opções de Rejeitar Chamadas, Ignorar Grupos e Sempre Online."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/settings/set/{instance_name}"
    
    payload = {
        "rejectCall": True,
        "msgCall": "Desculpe, este número é apenas para mensagens automáticas.",
        "groupsIgnore": True,
        "alwaysOnline": True,
        "readMessages": True,
        "readStatus": False,
        "syncFullHistory": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        if response.status_code in [200, 201]:
            return True, None
        return False, f"Evolution Status {response.status_code}: {response.text}"
    except Exception as e:
        logger.error(f"Erro ao configurar settings para {instance_name}: {e}")
        return False, str(e)
