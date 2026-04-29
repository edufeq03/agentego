import requests
import os
import logging

logger = logging.getLogger(__name__)

def enviar_whatsapp(numero, mensagem):
    url = os.getenv("EVOLUTION_URL")
    
    # Calcula um tempo de digitação natural (mínimo de 1s, mais 30ms por caractere da resposta, máximo de 4s)
    tempo_digitando = min(1000 + (len(mensagem) * 30), 4000)

    payload = {
        "number": numero,
        "text": mensagem,
        "delay": tempo_digitando
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        logger.info(f"[{numero}] Mensagem despachada para o WhatsApp com sucesso.")
    else:
        logger.error(f"[{numero}] FALHA NO ENVIO (Status {response.status_code}): {response.text}")