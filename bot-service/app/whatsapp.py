import requests
import os
import logging

logger = logging.getLogger(__name__)

from app import whatsapp_service

def enviar_whatsapp(numero, mensagem, instance_name):
    base_url = whatsapp_service.get_evolution_base_url()
    url = f"{base_url}/message/sendText/{instance_name}"
    
    payload = {
        "number": numero,
        "text": mensagem
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        logger.info(f"[{numero}] Mensagem despachada para o WhatsApp com sucesso (Instância: {instance_name}).")
    else:
        logger.error(f"[{numero}] FALHA NO ENVIO (Status {response.status_code}): {response.text}")

def simular_digitacao(numero, instance_name):
    base_url = whatsapp_service.get_evolution_base_url()
    url = f"{base_url}/chat/sendPresence/{instance_name}"
    
    payload = {
        "number": numero,
        "delay": 3000,
        "presence": "composing"
    }
    
    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=2)
    except Exception as e:
        logger.error(f"Erro ao simular digitação: {e}")

def simular_gravacao_audio(numero, instance_name):
    base_url = whatsapp_service.get_evolution_base_url()
    url = f"{base_url}/chat/sendPresence/{instance_name}"
    
    payload = {
        "number": numero,
        "delay": 5000,
        "presence": "recording"
    }
    
    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=2)
    except Exception as e:
        logger.error(f"Erro ao simular gravacao de audio: {e}")

def enviar_audio_whatsapp(numero, caminho_audio, instance_name):
    base_url = whatsapp_service.get_evolution_base_url()
    url = f"{base_url}/message/sendWhatsAppAudio/{instance_name}"
    
    import base64
    with open(caminho_audio, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        
    payload = {
        "number": numero,
        "audio": audio_audio_base64 if 'audio_audio_base64' in locals() else audio_base64,
        "delay": 1200,
        "encoding": True
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        logger.info(f"[{numero}] Áudio despachado para o WhatsApp com sucesso (Instância: {instance_name}).")
    else:
        logger.error(f"[{numero}] FALHA NO ENVIO DO ÁUDIO (Status {response.status_code}): {response.text}")