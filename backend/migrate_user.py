import os
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, Empresa, Usuario
from app.auth import get_password_hash

def migrate():
    db = SessionLocal()
    empresa = db.query(Empresa).filter(Empresa.nome == "Prime Fit").first()
    
    if not empresa:
        print("Empresa Prime Fit não encontrada.")
        return
        
    usuario = db.query(Usuario).filter(Usuario.email == "admin@primefit.com").first()
    if usuario:
        print("Usuário já existe.")
        return
        
    novo_usuario = Usuario(
        empresa_id=empresa.id,
        email="admin@primefit.com",
        senha_hash=get_password_hash("123456")
    )
    db.add(novo_usuario)
    db.commit()
    print("Usuário admin@primefit.com com senha 123456 criado com sucesso!")

if __name__ == "__main__":
    migrate()
