import os
import requests
import redis
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()

def check_db():
    print("--- [1/4] BANCO DE DADOS ---")
    url = os.getenv("DATABASE_URL")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexão com Postgres OK!")
    except Exception as e:
        print(f"❌ Erro no Postgres: {e}")

def check_redis():
    print("\n--- [2/4] REDIS ---")
    url = os.getenv("REDIS_URL")
    try:
        r = redis.from_url(url)
        r.ping()
        print("✅ Conexão com Redis OK!")
    except Exception as e:
        print(f"❌ Erro no Redis: {e}")

def check_openai():
    print("\n--- [3/4] OPENAI API ---")
    key = os.getenv("OPENAI_API_KEY")
    if not key or "sk-" not in key:
        print("❌ Chave OpenAI não configurada ou inválida no .env")
        return
    try:
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ OpenAI API Key é VÁLIDA!")
        else:
            print(f"❌ OpenAI retornou erro {response.status_code}: {response.json().get('error', {}).get('message')}")
    except Exception as e:
        print(f"❌ Falha ao conectar na OpenAI: {e}")

def check_evolution():
    print("\n--- [4/4] EVOLUTION API ---")
    url = os.getenv("EVOLUTION_URL")
    key = os.getenv("EVOLUTION_API_KEY")
    
    if not url or not key:
        print("❌ Configurações da Evolution faltando no .env")
        return
    
    try:
        # Tenta extrair a base URL da evolution
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_evolution = f"{parsed.scheme}://{parsed.netloc}"
        
        headers = {"apikey": key}
        response = requests.get(f"{base_evolution}/instance/fetchInstances", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Evolution API ({base_evolution}) acessível e API Key OK!")
        else:
            print(f"❌ Evolution retornou erro {response.status_code}. Verifique a API Key.")
    except Exception as e:
        print(f"❌ Falha ao conectar na Evolution: {e}")

if __name__ == "__main__":
    print("🔍 INICIANDO DIAGNÓSTICO DE INFRAESTRUTURA AGENTEGO\n")
    check_db()
    check_redis()
    check_openai()
    check_evolution()
    print("\n--- DIAGNÓSTICO CONCLUÍDO ---")
