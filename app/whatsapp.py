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

def simular_gravacao_audio(numero):
    url = os.getenv("EVOLUTION_URL")
    if not url: return
    
    url_presence = url.replace("message/sendText", "chat/sendPresence")
    
    payload = {
        "number": numero,
        "delay": 10000,
        "presence": "recording"
    }
    
    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }
    
    try:
        requests.post(url_presence, json=payload, headers=headers, timeout=2)
    except Exception as e:
        logger.error(f"Erro ao simular gravacao de audio: {e}")

def enviar_audio_whatsapp(numero, caminho_audio):
    url = os.getenv("EVOLUTION_URL").replace("message/sendText", "message/sendWhatsAppAudio")
    
    import base64
    with open(caminho_audio, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        
    base64_formatado = f"data:audio/mp3;base64,{audio_base64}"
    
    payload = {
        "number": numero,
        "audio": base64_formatado,
        "delay": 1200,
        "encoding": True
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        logger.info(f"[{numero}] Áudio de voz despachado para o WhatsApp com sucesso.")
    else:
        logger.error(f"[{numero}] FALHA NO ENVIO DO ÁUDIO (Status {response.status_code}): {response.text}")