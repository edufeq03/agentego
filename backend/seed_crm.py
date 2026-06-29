import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import uuid
import random
from datetime import datetime, timedelta

from app.database import Empresa, SessionLocal
from app.models.crm import CrmContact, CrmDeal, CrmActivity, CrmContext, CrmPipeline

def seed_crm():
    db = SessionLocal()
    
    # 1. Encontrar a empresa
    empresa = db.query(Empresa).filter(Empresa.slug == 'horizonte-viagens').first()
    if not empresa:
        print("Empresa horizonte-viagens não encontrada. Criando empresa fake.")
        empresa = Empresa(
            id=uuid.uuid4(),
            nome="Horizonte Viagens (Fake)",
            slug="horizonte-viagens",
            telefone_whatsapp="5511999999999",
            plano="pro",
            criado_em=datetime.utcnow()
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

        # Criar Configuracao e Usuario
        from app.models.tenant import Configuracao, Usuario
        from app.auth import get_password_hash
        
        config = Configuracao(empresa_id=empresa.id, config={"modulos_ativos": ["crm"]})
        db.add(config)
        
        usuario = Usuario(
            empresa_id=empresa.id,
            email="admin@horizonteviagens.com",
            senha_hash=get_password_hash("admin")
        )
        db.add(usuario)
        db.commit()

    print(f"Semeando dados CRM para a empresa: {empresa.nome} ({empresa.id})")

    # 2. Criar 5 Contatos Fake
    nomes = ["Carlos Santana", "Ana Júlia", "Marcos Paulo", "Fernanda Lima", "Beto Carreiro"]
    telefones = ["5511999990001", "5511999990002", "5511999990003", "5511999990004", "5511999990005"]
    contatos = []
    
    for i in range(5):
        partes = nomes[i].split(" ", 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ""
        
        contato = CrmContact(
            empresa_id=empresa.id,
            first_name=first_name,
            last_name=last_name,
            phone=telefones[i],
            email=f"contato{i}@email.com",
            source="Seed Script",
            status="client" if i % 2 == 0 else "lead"
        )
        db.add(contato)
        contatos.append(contato)
        
    db.commit()
    for c in contatos: db.refresh(c)
    
    print("Contatos criados.")

    # 2b. Criar um Pipeline Fake
    pipeline = CrmPipeline(
        empresa_id=empresa.id,
        name="Funil de Vendas",
        is_default=True,
        stages=[
            {"id": "new", "name": "Novos Leads"},
            {"id": "contact", "name": "Contato"},
            {"id": "proposal", "name": "Proposta"},
            {"id": "negotiation", "name": "Negociação"},
            {"id": "won", "name": "Ganho"}
        ]
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    
    # 3. Criar 5 Deals Fake
    stages = ['new', 'contact', 'proposal', 'negotiation', 'won']
    titulos = ["Pacote Europa", "Visto Americano", "Cruzeiro Bahamas", "Passagem Japão", "Seguro Viagem"]
    
    for i in range(5):
        deal = CrmDeal(
            empresa_id=empresa.id,
            pipeline_id=pipeline.id,
            contact_id=contatos[i].id,
            title=titulos[i],
            value=float(random.randint(1500, 15000)),
            stage_id=stages[i],
            status="open" if stages[i] != 'won' else "won"
        )
        db.add(deal)
        
        # Criar uma atividade (Nota) para cada
        act = CrmActivity(
            empresa_id=empresa.id,
            contact_id=contatos[i].id,
            deal_id=deal.id,
            type="note",
            subject=f"Interação inicial - {titulos[i]}",
            description="Cliente demonstrou interesse após ver o anúncio no Instagram.",
            done=True,
            done_at=datetime.utcnow() - timedelta(days=i)
        )
        db.add(act)
        
    # 4. Criar um contexto de IA fake para o primeiro contato
    ctx = CrmContext(
        empresa_id=empresa.id,
        contact_id=contatos[0].id,
        summary="O Carlos está planejando uma viagem para a Europa com a esposa no final do ano. Eles têm flexibilidade de datas, mas preferem não pegar muito frio. Orçamento em torno de R$ 30.000.",
        sentiment="Muito Positivo",
        tags=["Europa", "Casal", "Fim de Ano"],
        key_points=["Quer visitar Itália e França", "Evitar Dezembro se nevar muito"],
        last_analyzed_at=datetime.utcnow()
    )
    db.add(ctx)

    db.commit()
    print("Deals, Atividades e Contexto criados com sucesso!")
    # 5. Criar Leads e Mensagens para a aba de Conversas
    from app.models.atendimento import Lead, Mensagem

    # Verifica se já existem leads
    existing_leads = db.query(Lead).filter(Lead.empresa_id == empresa.id).count()
    if existing_leads == 0:
        lead1 = Lead(
            empresa_id=empresa.id,
            telefone="5511999990006",
            nome="João Pedro",
            stage="novo",
            visit_offer_made=False,
            canal_entrada="whatsapp"
        )
        db.add(lead1)
        db.commit()
        db.refresh(lead1)

        msg1 = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead1.id,
            tipo="usuario",
            mensagem="Olá, vi o anúncio no Instagram e gostaria de saber mais sobre pacotes para o Nordeste.",
            timestamp=datetime.utcnow() - timedelta(minutes=10)
        )
        msg2 = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead1.id,
            tipo="agente",
            mensagem="Olá João Pedro! Tudo bem? Temos pacotes incríveis para o Nordeste. Alguma preferência de estado?",
            timestamp=datetime.utcnow() - timedelta(minutes=5)
        )
        msg3 = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead1.id,
            tipo="usuario",
            mensagem="Eu gostaria de ir para Porto de Galinhas. Qual o valor aproximado para um casal?",
            timestamp=datetime.utcnow()
        )
        db.add(msg1)
        db.add(msg2)
        db.add(msg3)

        lead2 = Lead(
            empresa_id=empresa.id,
            telefone="5511999990007",
            nome="Mariana Costa",
            stage="interessado",
            visit_offer_made=False,
            canal_entrada="whatsapp"
        )
        db.add(lead2)
        db.commit()
        db.refresh(lead2)

        msg4 = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead2.id,
            tipo="usuario",
            mensagem="Vocês fazem emissão de passagens com milhas?",
            timestamp=datetime.utcnow()
        )
        db.add(msg4)

        db.commit()
        print("Leads e Mensagens (Conversas) criados com sucesso!")

    db.close()

if __name__ == "__main__":
    seed_crm()
