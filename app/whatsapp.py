import requests
import os
import logging

logger = logging.getLogger(__name__)

def enviar_whatsapp(numero, mensagem):
    url = os.getenv("EVOLUTION_URL")
    
    payload = {
        "number": numero,
        "text": mensagem
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        logger.info(f"[{numero}] Mensagem despachada para o WhatsApp com sucesso.")
    else:
        logger.error(f"[{numero}] FALHA NO ENVIO (Status {response.status_code}): {response.text}")

def simular_digitacao(numero):
    url = os.getenv("EVOLUTION_URL")
    if not url: return
    
    url_presence = url.replace("message/sendText", "chat/sendPresence")
    
    payload = {
        "number": numero,
        "delay": 6000,
        "presence": "composing"
    }
    
    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }
    
    try:
        # Usamos timeout baixo para não travar a aplicação caso a Evolution demore
        requests.post(url_presence, json=payload, headers=headers, timeout=2)
    except Exception as e:
        logger.error(f"Erro ao simular digitação: {e}")