from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load from the root .env
load_dotenv(dotenv_path="/home/capella/Documents/antigravity/agente_academia/.env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Query users
    from sqlalchemy import text
    result = session.execute(text("SELECT email, role FROM usuarios")).fetchall()
    
    if not result:
        print("Nenhum usuário encontrado no banco de dados.")
    else:
        print("Usuários cadastrados:")
        for row in result:
            print(f"- Email: {row[0]} | Role: {row[1]}")
    
    # Query empresas
    result_emp = session.execute(text("SELECT nome, slug FROM empresas")).fetchall()
    if result_emp:
        print("\nEmpresas cadastradas:")
        for row in result_emp:
            print(f"- Nome: {row[0]} | Slug: {row[1]}")

except Exception as e:
    print(f"Erro ao conectar ao banco: {e}")
