import os
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, Empresa

def list_companies():
    db = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        for emp in empresas:
            print(f"ID: {emp.id} | Nome: {emp.nome} | Token: {emp.webhook_token} | Ativo: {emp.ativo}")
    finally:
        db.close()

if __name__ == "__main__":
    list_companies()
