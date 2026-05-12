from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/capella/Documents/antigravity/agente_academia/.env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    from sqlalchemy import text
    result = session.execute(text("SELECT empresa_id, config FROM configuracoes")).fetchall()
    
    print("Configurações no banco:")
    for row in result:
        print(f"Empresa ID: {row[0]}")
        print(f"Config JSON: {json.dumps(row[1], indent=2)}")
        print("-" * 20)

except Exception as e:
    print(f"Erro: {e}")
