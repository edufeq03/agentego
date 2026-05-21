import sys
import os

# Configure imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../bot-service"))

from app.database import SessionLocal, Lead, LeadSeguro, Empresa
from app.agents.contexto_agent import contexto_agent
from app.agents.especialistas.corretora import EspecialistaCorretora

db = SessionLocal()
try:
    empresa = db.query(Empresa).filter(Empresa.nicho == "corretora").first()
    lead = db.query(Lead).filter(Lead.telefone == "5519996737713").first()
    lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()

    # Recreate the history exactly as in Turn 3
    historico = [
        {"role": "user", "content": "eae, qual o seu nome?"},
        {"role": "assistant", "content": "Olá! Eu sou a Alice, sua assistente virtual da Piccolo Seguros. Como posso te ajudar hoje? Você está interessado em algum tipo de seguro ou plano de saúde?"},
        {"role": "user", "content": "preciso de cotacao para plano de saúde"},
        {"role": "assistant", "content": "Ótimo! Para começar a cotação do plano de saúde, preciso de algumas informações. Qual é o seu nome?"}
    ]

    mensagem_usuario = "Eduardo Targine Capella"

    config = {
        "nome_agente": "Alice",
        "nome_empresa": empresa.nome,
        "nicho": "corretora"
    }

    triagem = {
        "intencao": "cotacao",
        "sentimento": "neutro",
        "urgente": False,
        "resumo_curto": "Quer plano de saúde"
    }

    ctx = contexto_agent.montar(
        empresa=empresa,
        lead=lead,
        lead_seguro=lead_seguro,
        triagem=triagem,
        config=config
    )

    especialista = EspecialistaCorretora()
    prompt = especialista._montar_prompt(ctx)

    # EXPERIMENT 4: No history, standard user message
    mensagens_4 = [{"role": "system", "content": prompt}]
    mensagens_4.append({"role": "user", "content": "Meu nome é Eduardo Targine Capella. Preciso de cotação de seguro."})
    
    from openai import OpenAI
    client = OpenAI()

    print("=== EXPERIMENTO 4: Sem histórico ===")
    res_4 = client.chat.completions.create(model="gpt-4o-mini", messages=mensagens_4, temperature=0.2)
    print("Resposta 4:", repr(res_4.choices[0].message.content))

finally:
    db.close()
