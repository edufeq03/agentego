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
    # Assume que a URL termina em /message/sendText/instancia
    if "/message/sendText" in url:
        return url.split("/message/sendText")[0]
    return url

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
            return response.json().get("instance", {}).get("state", "disconnected")
        if response.status_code == 404:
            return "not_found"
        return "disconnected"
    except Exception:
        return "disconnected"

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

def set_webhook(instance_name: str, webhook_url: str) -> bool:
    """Configura o webhook para a instância."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/webhook/set/{instance_name}"
    
    payload = {
        "url": webhook_url,
        "enabled": True,
        "events": [
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE",
            "SEND_MESSAGE",
            "CONNECTION_UPDATE"
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Erro ao configurar webhook para {instance_name}: {e}")
        return False

def logout_instance(instance_name: str) -> bool:
    """Desconecta o WhatsApp da instância."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/instance/logout/{instance_name}"
    
    try:
        response = requests.delete(url, headers=get_headers(), timeout=10)
        return response.status_code == 200
    except Exception:
        return False
