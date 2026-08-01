import sys
import os
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, Usuario, Empresa
from app.auth import get_password_hash

def reset_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            print(f"❌ Usuário com e-mail '{email}' não foi encontrado no banco restaurado.")
            print("\n📋 Usuários cadastrados no banco restaurado:")
            users = db.query(Usuario).all()
            for u in users:
                emp = db.query(Empresa).filter(Empresa.id == u.empresa_id).first()
                emp_nome = emp.nome if emp else 'N/A'
                print(f" - {u.email} (Empresa: {emp_nome}, Role: {getattr(u, 'role', 'client')})")
            return
        
        user.senha_hash = get_password_hash(new_password)
        db.commit()
        print(f"✅ Senha do usuário '{email}' redefinida com sucesso!")
        print(f"E-mail: {email}")
        print(f"Nova Senha: {new_password}")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao redefinir senha: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("=== Utilitário de Redefinição de Senha ===")
        print("Uso: python reset_password.py <email> <nova_senha>\n")
        print("📋 Usuários atualmente cadastrados no banco:")
        db = SessionLocal()
        users = db.query(Usuario).all()
        for u in users:
            emp = db.query(Empresa).filter(Empresa.id == u.empresa_id).first()
            emp_nome = emp.nome if emp else 'N/A'
            print(f" - {u.email} (Empresa: {emp_nome})")
        db.close()
    else:
        reset_password(sys.argv[1], sys.argv[2])
