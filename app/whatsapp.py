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

    response = requests.post(url, json=payload, headers=headers)
    
    print("=== DEBUG EVOLUTION API ===")
    print(f"Enviando para: {url}")
    print(f"Payload: {payload}")
    print(f"Status Code: {response.status_code}")
    print(f"Resposta API: {response.text}")
    print("===========================")