import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, Conversa, Mensagem, Transbordo

# Conecta ao banco de dados usando a URL do .env ou localhost para testes locais
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_seed():
    db = SessionLocal()

    # Cria as tabelas se não existirem
    Base.metadata.create_all(bind=engine)

    # Verifica se já existe a conversa teste
    telefone_teste = "5511999999999"
    conversa_existente = db.query(Conversa).filter(Conversa.telefone == telefone_teste).first()

    if not conversa_existente:
        print("Criando conversa de teste...")
        nova_conversa = Conversa(telefone=telefone_teste)
        db.add(nova_conversa)
        db.commit()
        db.refresh(nova_conversa)

        print("Adicionando mensagens de teste...")
        m1 = Mensagem(conversa_id=nova_conversa.id, tipo="usuario", mensagem="Olá, gostaria de saber os preços")
        m2 = Mensagem(conversa_id=nova_conversa.id, tipo="agente", mensagem="Olá! Nossos planos começam em R$ 80,00.")
        db.add_all([m1, m2])
        db.commit()

        print("Adicionando status de transbordo de teste...")
        t1 = Transbordo(telefone=telefone_teste, status="aguardando")
        db.add(t1)
        db.commit()

        print("Seed concluído com sucesso!")
    else:
        print("Dados de teste já existem. Nenhuma ação necessária.")

    db.close()

if __name__ == "__main__":
    print(f"Conectando ao banco de dados em {DATABASE_URL}...")
    try:
        run_seed()
    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
