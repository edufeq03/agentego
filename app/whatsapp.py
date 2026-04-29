import requests
import os

def enviar_whatsapp(numero, mensagem):
    url = os.getenv("EVOLUTION_URL")

    payload = {
        "number": numero,
        "text": mensagem
    }

    headers = {
        "apikey": os.getenv("EVOLUTION_API_KEY")
    }

    requests.post(url, json=payload, headers=headers)