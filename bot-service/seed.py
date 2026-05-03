import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, Empresa, Configuracao, Lead, Mensagem, Evento

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_seed():
    db = SessionLocal()

    # Cria as tabelas se não existirem
    Base.metadata.create_all(bind=engine)

    telefone_empresa = "5511999990000"
    empresa_existente = db.query(Empresa).filter(Empresa.telefone_whatsapp == telefone_empresa).first()

    if not empresa_existente:
        print("Criando Empresa 'Prime Fit'...")
        nova_empresa = Empresa(
            nome="Prime Fit",
            telefone_whatsapp=telefone_empresa,
            webhook_token="primefit-token-123" # Token estático para facilitar testes
        )
        db.add(nova_empresa)
        db.commit()
        db.refresh(nova_empresa)

        print("Adicionando Configuração da Empresa...")
        config_data = {
            "nome_agente": "Rosana",
            "nome_empresa": "Prime Fit",
            "planos": { "basico": 80, "vip": 150 },
            "horarios": { "semana": "08:00 as 22:00", "sabado": "09:00 as 13:00" },
            "endereco": "Av. Eng. Antônio Francisco de Paula Souza, 123 - Campinas",
            "pagamentos": ["Pix", "Cartão de Crédito", "Dinheiro"],
            "aulas_vip": ["Spinning", "Zumba", "Funcional", "Fitdance"]
        }
        nova_config = Configuracao(empresa_id=nova_empresa.id, config=config_data)
        db.add(nova_config)
        db.commit()

        print("Criando Lead de teste...")
        novo_lead = Lead(empresa_id=nova_empresa.id, telefone="5511999999999", stage="curioso")
        db.add(novo_lead)
        db.commit()
        db.refresh(novo_lead)

        print("Adicionando histórico de mensagens de teste...")
        m1 = Mensagem(empresa_id=nova_empresa.id, lead_id=novo_lead.id, tipo="usuario", mensagem="Olá, gostaria de saber os preços", intencao="preco")
        m2 = Mensagem(empresa_id=nova_empresa.id, lead_id=novo_lead.id, tipo="agente", mensagem="Olá! Nossos planos começam em R$ 80,00 mensais no básico.")
        db.add_all([m1, m2])
        db.commit()

        print("Adicionando evento de teste...")
        e1 = Evento(empresa_id=nova_empresa.id, lead_id=novo_lead.id, tipo="perguntou_preco")
        db.add(e1)
        db.commit()

        print(f"Seed concluído com sucesso!")
        print(f"Webhook URL para testes: http://localhost:8000/webhook/{nova_empresa.webhook_token}")
    else:
        print("Dados da Prime Fit já existem. Nenhuma ação necessária.")
        print(f"Webhook URL para testes: http://localhost:8000/webhook/{empresa_existente.webhook_token}")

    db.close()

if __name__ == "__main__":
    print(f"Conectando ao banco de dados em {DATABASE_URL}...")
    try:
        run_seed()
    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
