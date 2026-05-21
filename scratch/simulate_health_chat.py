import sys
import os

# Configure imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../bot-service"))

from app.database import SessionLocal, Lead, LeadSeguro, Empresa, Mensagem, Evento
from app.pipeline import processar_webhook
import uuid

db = SessionLocal()
try:
    # 1. Setup fresh test data
    empresa = db.query(Empresa).filter(Empresa.nicho == "corretora").first()
    if not empresa:
        print("Empresa não encontrada.")
        sys.exit(1)

    # Clean old test leads for this phone
    telefone_teste = "5519996737713"
    leads = db.query(Lead).filter(Lead.telefone == telefone_teste).all()
    for l in leads:
        db.query(Evento).filter(Evento.lead_id == l.id).delete()
        db.query(Mensagem).filter(Mensagem.lead_id == l.id).delete()
        db.query(LeadSeguro).filter(LeadSeguro.id == l.id).delete()
        db.delete(l)
    db.commit()

    # Create fresh lead
    lead = Lead(empresa_id=empresa.id, telefone=telefone_teste, stage="novo")
    db.add(lead)
    db.commit()
    db.refresh(lead)

    lead_seguro = LeadSeguro(id=lead.id, empresa_id=empresa.id, telefone=lead.telefone, stage="novo")
    db.add(lead_seguro)
    db.commit()
    db.refresh(lead_seguro)

    turns = [
        "eae, qual o seu nome?",
        "preciso de cotacao para plano de saúde",
        "Eduardo Targine Capella",
        "41 anos",
        "nenhum dos dois",
        "sim, Unimed",
        "região de Campinas"
    ]

    print("=== INICIANDO SIMULAÇÃO DE CHAT DE SAÚDE TURNO POR TURNO ===")
    for i, msg in enumerate(turns):
        print(f"\n--- Turno {i+1} ---")
        print(f"Cliente: '{msg}'")
        
        # Let's inspect the inputs to processar_webhook
        # We can hook into get_especialista or just let processar_webhook run and check
        res = processar_webhook(empresa, telefone_teste, msg)
        
        # Find raw message saved in Mensagem table
        last_agent_msg = db.query(Mensagem).filter(
            Mensagem.lead_id == lead.id,
            Mensagem.tipo == "agente"
        ).order_by(Mensagem.timestamp.desc()).first()
        
        print(f"Mensagem no Banco (tipo=agente): {repr(last_agent_msg.mensagem if last_agent_msg else None)}")
        print(f"IA (Resposta Limpa): {repr(res.get('resposta'))}")
        
        # Busca estado atualizado do banco
        db.refresh(lead_seguro)
        
        print(f"Status do Pipeline: {res.get('status')}")
        print(f"Campos atualizados no Banco:")
        print(f"  - nome_segurado: {lead_seguro.nome_segurado}")
        print(f"  - tipo_seguro: {lead_seguro.tipo_seguro}")
        print(f"  - idade_segurado: {lead_seguro.idade_segurado}")
        print(f"  - tem_cnpj: {lead_seguro.tem_cnpj}")
        print(f"  - e_mei: {lead_seguro.e_mei}")
        print(f"  - tem_plano_anterior: {lead_seguro.tem_plano_anterior}")
        print(f"  - plano_anterior_nome: {lead_seguro.plano_anterior_nome}")
        print(f"  - regiao: {lead_seguro.regiao}")

finally:
    db.close()
