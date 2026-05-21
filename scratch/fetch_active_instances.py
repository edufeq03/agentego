import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Setup headers for Evolution API
evolution_url = os.getenv("EVOLUTION_URL", "")
# Extract base url
if "/message/sendText" in evolution_url:
    base_url = evolution_url.split("/message/sendText")[0].rstrip("/")
else:
    base_url = evolution_url.rstrip("/")

api_key = os.getenv("EVOLUTION_API_KEY")
headers = {
    "apikey": api_key,
    "Content-Type": "application/json"
}

print(f"Base URL: {base_url}")

try:
    fetch_url = f"{base_url}/instance/fetchInstances"
    res = requests.get(fetch_url, headers=headers, timeout=10)
    print(f"Fetch Status Code: {res.status_code}")
    if res.status_code == 200:
        instances = res.json()
        print(f"Total instances found: {len(instances)}")
        for inst in instances:
            name = inst.get("instanceName") or inst.get("name")
            status = inst.get("status") or inst.get("connectionStatus")
            print(f"\n- Instância: {name} (Status: {status})")
            
            # Find webhook
            webhook_find_url = f"{base_url}/webhook/find/{name}"
            try:
                res_wh = requests.get(webhook_find_url, headers=headers, timeout=5)
                if res_wh.status_code == 200:
                    print(f"  Webhook: {json.dumps(res_wh.json(), indent=2)}")
                else:
                    print(f"  Webhook Error {res_wh.status_code}: {res_wh.text}")
            except Exception as e:
                print(f"  Erro ao buscar webhook para {name}: {e}")
    else:
        print(f"Error fetching instances: {res.text}")
except Exception as e:
    print(f"Erro: {e}")
