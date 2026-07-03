import os
import logging
from typing import Optional, Dict, Any
import requests

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
    """Cria uma nova instância na Evolution API via Dispatcher."""
    from app.whatsapp.dispatcher import get_dispatcher
    dispatcher = get_dispatcher()
    return dispatcher.criar_instancia("evolution", instance_name)

def get_connection_status(instance_name: str) -> str:
    """Retorna o status da conexão via Dispatcher."""
    from app.whatsapp.dispatcher import get_dispatcher
    dispatcher = get_dispatcher()
    return dispatcher.status_conexao("evolution", instance_name)

def get_qrcode(instance_name: str) -> Optional[str]:
    """Retorna o base64 do QR Code para conexão via Dispatcher."""
    from app.whatsapp.dispatcher import get_dispatcher
    dispatcher = get_dispatcher()
    return dispatcher.get_qrcode("evolution", instance_name)

def set_webhook(instance_name: str, webhook_url: str):
    """Configura o webhook para a instância via Dispatcher."""
    from app.whatsapp.dispatcher import get_dispatcher
    dispatcher = get_dispatcher()
    return dispatcher.configurar_webhook("evolution", instance_name, webhook_url)

def find_webhook(instance_name: str) -> Optional[str]:
    """Busca a URL do webhook atualmente configurada na instância."""
    base_url = get_evolution_base_url()
    url = f"{base_url}/webhook/find/{instance_name}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            data = response.json()
            # A Evolution retorna uma lista de webhooks ou um objeto dependendo da versão
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("url")
            return data.get("url")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar webhook para {instance_name}: {e}")
        return None

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
