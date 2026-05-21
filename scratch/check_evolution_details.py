import os
import requests
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Setup database
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

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
    from sqlalchemy import text
    companies = session.execute(text("SELECT id, nome, evolution_instance, webhook_token, nicho FROM empresas WHERE ativo = true")).fetchall()
    
    for company in companies:
        comp_id, nome, instance, token, nicho = company
        print(f"\n========================================")
        print(f"Empresa: {nome} (Nicho: {nicho})")
        print(f"ID: {comp_id}")
        print(f"Instância: {instance}")
        print(f"Token Webhook: {token}")
        
        if not instance:
            print("Nenhuma instância cadastrada.")
            continue
            
        # Get Connection status
        conn_url = f"{base_url}/instance/connectionState/{instance}"
        try:
            res_conn = requests.get(conn_url, headers=headers, timeout=5)
            print(f"Connection Status Code: {res_conn.status_code}")
            if res_conn.status_code == 200:
                print(f"Connection Body: {json.dumps(res_conn.json(), indent=2)}")
            else:
                print(f"Connection Error: {res_conn.text}")
        except Exception as e:
            print(f"Erro ao buscar status de conexão: {e}")
            
        # Get Webhook status
        webhook_find_url = f"{base_url}/webhook/find/{instance}"
        try:
            res_wh = requests.get(webhook_find_url, headers=headers, timeout=5)
            print(f"Webhook Find Status Code: {res_wh.status_code}")
            if res_wh.status_code == 200:
                print(f"Webhook Body: {json.dumps(res_wh.json(), indent=2)}")
            else:
                print(f"Webhook Error: {res_wh.text}")
        except Exception as e:
            print(f"Erro ao buscar webhook: {e}")
            
except Exception as e:
    print(f"Erro ao acessar banco: {e}")
finally:
    session.close()
