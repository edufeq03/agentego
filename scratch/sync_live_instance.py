import os
import sys
import requests
import json
from dotenv import load_dotenv

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../bot-service')))

load_dotenv()

from app import whatsapp_service

instance_name = "inst-piccoloseguros-b1e0"
webhook_url = "https://sites-academia-bot.zdgx3l.easypanel.host/webhook/e4023260-5088-48ca-97c5-ccd3c5c3d9eb"

print(f"Sincronizando webhook para a instância {instance_name}...")
print(f"URL do Webhook: {webhook_url}")

success, error = whatsapp_service.set_webhook(instance_name, webhook_url)

if success:
    print("✅ Sincronização enviada com sucesso para a Evolution API!")
else:
    print(f"❌ Erro ao enviar sincronização: {error}")

# Agora vamos verificar as configurações da instância diretamente no servidor da Evolution API
evolution_url = os.getenv("EVOLUTION_URL", "")
if "/message/sendText" in evolution_url:
    base_url = evolution_url.split("/message/sendText")[0].rstrip("/")
else:
    base_url = evolution_url.rstrip("/")

api_key = os.getenv("EVOLUTION_API_KEY")
headers = {
    "apikey": api_key,
    "Content-Type": "application/json"
}

webhook_find_url = f"{base_url}/webhook/find/{instance_name}"
try:
    res_wh = requests.get(webhook_find_url, headers=headers, timeout=5)
    if res_wh.status_code == 200:
        print("\n🔍 Configuração do Webhook atual no Servidor:")
        print(json.dumps(res_wh.json(), indent=2))
    else:
        print(f"\n❌ Erro ao ler configuração do Webhook: {res_wh.status_code} - {res_wh.text}")
except Exception as e:
    print(f"\n❌ Erro de rede ao buscar webhook: {e}")
