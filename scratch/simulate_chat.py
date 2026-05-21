import sys
import os

# Configure imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../bot-service"))

from app.database import SessionLocal, Lead, LeadSeguro, Empresa, Mensagem
from app.agent import processar_mensagem_dinamica
from app.pipeline import _processar_tags

db = SessionLocal()
try:
    # 1. Setup mock/real data
    empresa = db.query(Empresa).filter(Empresa.nicho == "corretora").first()
    if not empresa:
        print("Nenhuma empresa de corretora no banco local. Criando uma para o teste...")
        empresa = Empresa(nome="Piccolo Seguros Teste", slug="piccolo-seguros-teste", telefone_whatsapp="5519996737713", nicho="corretora")
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

    lead = db.query(Lead).filter(Lead.telefone == "5519996737713").first()
    if not lead:
        lead = Lead(empresa_id=empresa.id, telefone="5519996737713", stage="novo")
        db.add(lead)
        db.commit()
        db.refresh(lead)

    lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
    if not lead_seguro:
        lead_seguro = LeadSeguro(id=lead.id, empresa_id=empresa.id, telefone=lead.telefone, stage="novo")
        db.add(lead_seguro)
        db.commit()
        db.refresh(lead_seguro)

    # Recreate history
    historico = [
        {"role": "user", "content": "Preciso de seguro pro meu carro"},
        {"role": "assistant", "content": "Claro! Para começarmos, você poderia me informar a marca e o modelo do seu carro?\n\n[ATUALIZAR_LEAD: tipo_seguro=auto]"},
    ]

    mensagem_usuario = "Gol g3 trend 2portas"
    
    config = {
        "nome_agente": "Rosana",
        "nome_empresa": empresa.nome,
        "nicho": "corretora"
    }

    print("=== SIMULANDO CHAMADA COM 'Gol g3 trend 2portas' ===")
    
    # Let's print the actual prompt that is generated!
    from app.agents.contexto_agent import contexto_agent
    from app.agents.especialistas.corretora import EspecialistaCorretora
    
    triagem = {
        "intencao": "duvida",
        "sentimento": "neutro",
        "urgente": False,
        "resumo_curto": ""
    }
    
    ctx = contexto_agent.montar(
        empresa=empresa,
        lead=lead,
        lead_seguro=lead_seguro,
        triagem=triagem,
        config=config
    )
    
    especialista = EspecialistaCorretora()
    prompt_ctx = especialista._montar_prompt(ctx)
    print("\n--- PROMPT GERADO QUE SERÁ ENVIADO PARA A IA ---")
    print(prompt_ctx)
    print("------------------------------------------------\n")
    
    mensagem_usuario_remind = mensagem_usuario + "\n\n(Lembrete do Sistema: Lembre-se de incluir a tag [ATUALIZAR_LEAD: campo=valor] ao final do seu texto se eu tiver acabado de te fornecer um dado!)"
    
    resposta_raw, t_in, t_out = processar_mensagem_dinamica(
        mensagem_usuario=mensagem_usuario_remind,
        config=config,
        intencao="duvida",
        stage=lead.stage,
        contexto_tempo="Quarta-feira 22:47 - Status: FECHADO",
        historico=historico,
        sentimento="neutro",
        empresa=empresa,
        lead=lead,
        lead_seguro=lead_seguro
    )

    print("\n--- RESPOSTA RAW DA IA ---")
    print(repr(resposta_raw))

    print("\n--- PROCESSANDO TAGS ---")
    _processar_tags(db, empresa, lead, resposta_raw, lead.telefone)
    
    # Reload from DB
    db.refresh(lead_seguro)
    print(f"Resultado no Banco -> marca_modelo: {lead_seguro.marca_modelo}")

finally:
    db.close()
