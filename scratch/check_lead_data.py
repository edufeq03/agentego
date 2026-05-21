import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../bot-service"))

from app.database import SessionLocal, Lead, LeadSeguro, Empresa

db = SessionLocal()
try:
    print("=== ÚLTIMOS 10 LEADS NO BANCO ===")
    leads = db.query(Lead).order_by(Lead.data_criacao.desc() if hasattr(Lead, "data_criacao") else Lead.id).limit(10).all()
    for l in leads:
        empresa = db.query(Empresa).filter(Empresa.id == l.empresa_id).first()
        empresa_nome = empresa.nome if empresa else "Desconhecida"
        print(f"ID: {l.id} | Telefone: {l.telefone} | Nome: {l.nome} | Stage: {l.stage} | Empresa: {empresa_nome}")
        
        ls = db.query(LeadSeguro).filter(LeadSeguro.id == l.id).first()
        if ls:
            print(f"  -> LeadSeguro: tipo_seguro={ls.tipo_seguro}, marca_modelo={ls.marca_modelo}, ano_fabricacao={ls.ano_fabricacao}, stage={ls.stage}")
        else:
            print("  -> LeadSeguro: não criado")
finally:
    db.close()
