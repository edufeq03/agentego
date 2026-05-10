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

    # 1. Definição do Template Estruturado de Academia (Novo Formato)
    config_academia = {
        "identidade": {
            "nome": "Rosana",
            "cargo": "Personal Trainer Virtual",
            "empresa": "Prime Fit",
            "missao": "Motivar e guiar alunos na jornada fitness, esclarecendo dúvidas sobre planos e treinos.",
            "tom_voz": "Entusiasta, motivador e empático."
        },
        "conhecimento": {
            "planos": [
                {"nome": "Básico", "valor": "R$ 80/mês", "beneficios": "Acesso à musculação"},
                {"nome": "VIP", "valor": "R$ 150/mês", "beneficios": "Musculação + Aulas (Zumba, Yoga, Crossfit)"}
            ],
            "horarios": "Seg-Sex: 06h às 22h | Sáb: 08h às 14h",
            "professores": [
                {"nome": "Marcos Silva", "especialidade": "Hipertrofia"},
                {"nome": "Ana Beatriz", "especialidade": "Yoga e Pilates"}
            ],
            "endereco": "Av. Eng. Antônio Francisco de Paula Souza, 123 - Campinas"
        }
    }

    # 2. Definição de uma Imobiliária (Novo Nicho)
    config_imobiliaria = {
        "identidade": {
            "nome": "Roberto",
            "cargo": "Consultor Imobiliário",
            "empresa": "Viver Bem Imóveis",
            "missao": "Ajudar clientes a encontrarem o imóvel ideal com segurança e transparência.",
            "tom_voz": "Profissional, sério e muito atencioso aos detalhes."
        },
        "conhecimento": {
            "oportunidades": [
                {"tipo": "Apartamento", "bairro": "Cambuí", "valor": "R$ 750.000"},
                {"tipo": "Casa", "bairro": "Taquaral", "valor": "R$ 1.200.000"}
            ],
            "servicos": ["Venda", "Locação", "Avaliação de Imóveis"],
            "horarios": "Segunda a Sexta das 09:00 às 18:00",
            "documentacao": "Trabalhamos com toda a assessoria para financiamento bancário."
        },
        "regras": [
            "Sempre pergunte qual o objetivo do cliente (comprar ou alugar).",
            "Pergunte a faixa de preço que o cliente está buscando.",
            "Convide para uma visita ao showroom."
        ]
    }

    # --- Criando Empresa 1 (Academia) ---
    from app.auth import get_password_hash
    from app.database import Usuario

    tel_academia = "5511999990000"
    emp_academia = db.query(Empresa).filter(Empresa.telefone_whatsapp == tel_academia).first()
    if not emp_academia:
        emp_academia = Empresa(nome="Prime Fit", telefone_whatsapp=tel_academia, webhook_token="primefit-token-123")
        db.add(emp_academia)
        db.commit()
        db.refresh(emp_academia)
    
    # Configuração Academia (Update ou Create)
    conf_academia = db.query(Configuracao).filter(Configuracao.empresa_id == emp_academia.id).first()
    if conf_academia:
        conf_academia.config = config_academia
    else:
        db.add(Configuracao(empresa_id=emp_academia.id, config=config_academia))
    
    # Usuário Academia
    user_academia = db.query(Usuario).filter(Usuario.email == "academia@teste.com").first()
    if not user_academia:
        db.add(Usuario(empresa_id=emp_academia.id, email="academia@teste.com", senha_hash=get_password_hash("senha123")))
    
    db.commit()

    # --- Criando Empresa 2 (Imobiliária) ---
    tel_imobiliaria = "5511988880000"
    emp_imob = db.query(Empresa).filter(Empresa.telefone_whatsapp == tel_imobiliaria).first()
    if not emp_imob:
        emp_imob = Empresa(nome="Viver Bem Imóveis", telefone_whatsapp=tel_imobiliaria, webhook_token="viverbem-token-456")
        db.add(emp_imob)
        db.commit()
        db.refresh(emp_imob)
    
    # Configuração Imobiliária (Update ou Create)
    conf_imob = db.query(Configuracao).filter(Configuracao.empresa_id == emp_imob.id).first()
    if conf_imob:
        conf_imob.config = config_imobiliaria
    else:
        db.add(Configuracao(empresa_id=emp_imob.id, config=config_imobiliaria))

    # Usuário Imobiliária
    user_imob = db.query(Usuario).filter(Usuario.email == "imoveis@teste.com").first()
    if not user_imob:
        db.add(Usuario(empresa_id=emp_imob.id, email="imoveis@teste.com", senha_hash=get_password_hash("senha123")))
    
    db.commit()

    print(f"Seed concluído! Temos 2 empresas de nichos diferentes.")
    print(f"Webhook Academia: http://localhost:8000/webhook/{emp_academia.webhook_token}")
    print(f"Webhook Imobiliária: http://localhost:8000/webhook/{emp_imob.webhook_token}")

    db.close()

if __name__ == "__main__":
    print(f"Conectando ao banco de dados em {DATABASE_URL}...")
    try:
        run_seed()
    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
