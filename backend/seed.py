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
    from app.database import init_db
    init_db()

    db = SessionLocal()

    # Cria as tabelas se não existirem
    Base.metadata.create_all(bind=engine)

    # 1. Definição do Template
    config_academia = {
        "nome_agente": "Rosana",
        "cargo_agente": "Personal Trainer Virtual",
        "nome_empresa": "Prime Fit",
        "missao": "Motivar e guiar alunos na jornada fitness, oferecendo suporte rápido e agendamento de aulas.",
        "tom_voz": "Energético, motivador e muito amigável.",
        "planos": {"basico": 89, "vip": 149},
        "horarios": {"semana": "06h às 22h", "sabado": "08h às 14h"},
        "pagamentos": ["Cartão", "Pix", "Dinheiro"],
        "endereco": "Av. Eng. Antônio Francisco de Paula Souza, 123 - Campinas",
        "professores": [
            {"nome": "Ricardo Silva", "especialidade": "Musculação e Hipertrofia"},
            {"nome": "Ana Beatriz", "especialidade": "Yoga e Pilates"}
        ]
    }

    # 2. Definição de uma Imobiliária (Novo Nicho)
    config_imobiliaria = {
        "nome_agente": "Roberto",
        "cargo_agente": "Consultor Imobiliário",
        "nome_empresa": "Viver Bem Imóveis",
        "missao": "Ajudar clientes a encontrarem o imóvel ideal com segurança e transparência.",
        "tom_voz": "Profissional, sério e muito atencioso aos detalhes.",
        "servicos": ["Venda", "Locação", "Avaliação de Imóveis"],
        "horarios": "Segunda a Sexta das 09:00 às 18:00",
        "documentacao": "Trabalhamos com toda a assessoria para financiamento bancário.",
        "oportunidades": [
            {"tipo": "Apartamento", "bairro": "Cambuí", "valor": "R$ 750.000"},
            {"tipo": "Casa", "bairro": "Taquaral", "valor": "R$ 1.200.000"}
        ],
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
        emp_academia = Empresa(nome="Prime Fit", slug="prime-fit", telefone_whatsapp=tel_academia, webhook_token="primefit-token-123", nicho="academia")
        db.add(emp_academia)
        db.commit()
        db.refresh(emp_academia)
    else:
        emp_academia.nicho = "academia"
        emp_academia.slug = "prime-fit"
        db.commit()
    
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
        emp_imob = Empresa(nome="Viver Bem Imóveis", slug="viver-bem-imoveis", telefone_whatsapp=tel_imobiliaria, webhook_token="viverbem-token-456", nicho="imobiliaria")
        db.add(emp_imob)
        db.commit()
        db.refresh(emp_imob)
    else:
        emp_imob.nicho = "imobiliaria"
        emp_imob.slug = "viver-bem-imoveis"
        db.commit()
    
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

    # --- Criando Empresa 3 (Beleza e Estética) ---
    config_beleza = {
        "nome_agente": "Juliana",
        "cargo_agente": "Especialista em Beleza Virtual",
        "nome_empresa": "Studio Elegance",
        "missao": "Proporcionar autoestima e bem-estar através de cuidados personalizados de beleza e estética.",
        "tom_voz": "Caloroso, sofisticado e acolhedor.",
        "horarios": {"semana": "09h às 20h", "sabado": "09h às 18h"},
        "endereco": "Av. Paulista, 1000 - Bela Vista - São Paulo",
        "agenda": {
            "aprovacao_manual": False,
            "whatsapp_profissional": "5511977770000",
            "lembrete_cliente_min": 60,
            "lembrete_profissional_hora": "08:00",
            "aprovacao_timeout_min": 60
        }
    }

    tel_beleza = "5511977770000"
    emp_beleza = db.query(Empresa).filter(Empresa.telefone_whatsapp == tel_beleza).first()
    if not emp_beleza:
        emp_beleza = Empresa(nome="Studio Elegance", slug="studio-elegance", telefone_whatsapp=tel_beleza, webhook_token="studioelegance-token-789", nicho="beleza")
        db.add(emp_beleza)
        db.commit()
        db.refresh(emp_beleza)
    else:
        emp_beleza.nicho = "beleza"
        emp_beleza.slug = "studio-elegance"
        db.commit()

    # Configuração Beleza
    conf_beleza = db.query(Configuracao).filter(Configuracao.empresa_id == emp_beleza.id).first()
    if conf_beleza:
        conf_beleza.config = config_beleza
    else:
        db.add(Configuracao(empresa_id=emp_beleza.id, config=config_beleza))

    # Usuário Beleza
    user_beleza = db.query(Usuario).filter(Usuario.email == "beleza@teste.com").first()
    if not user_beleza:
        db.add(Usuario(empresa_id=emp_beleza.id, email="beleza@teste.com", senha_hash=get_password_hash("senha123")))

    # Serviços Padrão Beleza
    from app.database import Servico
    servicos_padrao = [
        {
            "nome": "Corte Feminino",
            "descricao": "Corte de cabelo feminino personalizado.",
            "duracao_min": 60,
            "preco": 120.00,
            "ativo": True,
            "cor": "#8b5cf6",
            "ordem": 1,
            "tem_variacao_caracteristica": True,
            "caracteristicas": {
                "curto": {"duracao": 45, "preco": 100.00},
                "longo": {"duracao": 75, "preco": 150.00}
            },
            "recorrencia_sugerida_dias": 30
        },
        {
            "nome": "Escova",
            "descricao": "Lavagem e escova modeladora.",
            "duracao_min": 30,
            "preco": 60.00,
            "ativo": True,
            "cor": "#ec4899",
            "ordem": 2,
            "tem_variacao_caracteristica": True,
            "caracteristicas": {
                "curto": {"duracao": 30, "preco": 50.00},
                "longo": {"duracao": 45, "preco": 80.00}
            },
            "recorrencia_sugerida_dias": 7
        },
        {
            "nome": "Manicure",
            "descricao": "Cuidado das unhas das mãos com cutilagem e esmaltação.",
            "duracao_min": 45,
            "preco": 45.00,
            "ativo": True,
            "cor": "#10b981",
            "ordem": 3,
            "tem_variacao_caracteristica": False,
            "caracteristicas": None,
            "recorrencia_sugerida_dias": 14
        },
        {
            "nome": "Designer de Sobrancelhas",
            "descricao": "Design personalizado de sobrancelhas.",
            "duracao_min": 30,
            "preco": 50.00,
            "ativo": True,
            "cor": "#3b82f6",
            "ordem": 4,
            "tem_variacao_caracteristica": False,
            "caracteristicas": None,
            "recorrencia_sugerida_dias": 21
        }
    ]

    for s_info in servicos_padrao:
        s_obj = db.query(Servico).filter(Servico.empresa_id == emp_beleza.id, Servico.nome == s_info["nome"]).first()
        if not s_obj:
            s_obj = Servico(
                empresa_id=emp_beleza.id,
                nome=s_info["nome"],
                descricao=s_info["descricao"],
                duracao_min=s_info["duracao_min"],
                preco=s_info["preco"],
                ativo=s_info["ativo"],
                cor=s_info["cor"],
                ordem=s_info["ordem"],
                tem_variacao_caracteristica=s_info["tem_variacao_caracteristica"],
                caracteristicas=s_info["caracteristicas"],
                recorrencia_sugerida_dias=s_info["recorrencia_sugerida_dias"]
            )
            db.add(s_obj)

    db.commit()

    print(f"Seed concluído! Temos 3 empresas de nichos diferentes.")
    print(f"Webhook Academia: http://localhost:8000/webhook/{emp_academia.webhook_token}")
    print(f"Webhook Imobiliária: http://localhost:8000/webhook/{emp_imob.webhook_token}")
    print(f"Webhook Beleza: http://localhost:8000/webhook/{emp_beleza.webhook_token}")

    db.close()

if __name__ == "__main__":
    print(f"Conectando ao banco de dados em {DATABASE_URL}...")
    try:
        run_seed()
    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
