import os
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, Empresa, Configuracao

def check_company(company_id):
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.id == company_id).first()
        if not empresa:
            print(f"Empresa {company_id} não encontrada.")
            return
        
        print(f"Empresa: {empresa.nome}")
        print(f"Ativa: {empresa.ativo}")
        print(f"Instance: {empresa.evolution_instance}")
        print(f"Webhook Token: {empresa.webhook_token}")
        
        config = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
        if config:
            print(f"Config: {config.config}")
        else:
            print("Config não encontrada.")
            
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else "9c8ab728-aaaa-4454-90b8-4d06afd827db"
    check_company(cid)
