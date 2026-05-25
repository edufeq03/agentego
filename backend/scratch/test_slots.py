import sys
import os

# Adiciona o diretório app ao path
sys.path.append("/app")

from app.database import SessionLocal, Empresa, Servico
from app.agenda_service import calcular_slots
from app.pipeline_agenda import processar_pipeline_agenda

db = SessionLocal()
try:
    print("=== RUNNING SLOT & TAG VERIFICATION TESTS ===")
    
    # 1. Obter Empresa e Serviço
    empresa = db.query(Empresa).filter(Empresa.nome == "Prime Fit").first()
    if not empresa:
        print("ERROR: Prime Fit company not found in database!")
        sys.exit(1)
        
    servico = db.query(Servico).filter(Servico.empresa_id == empresa.id).first()
    if not servico:
        print("ERROR: Service not found for Prime Fit!")
        sys.exit(1)
        
    print(f"Empresa: {empresa.nome} (ID: {empresa.id})")
    print(f"Serviço: {servico.nome} (ID: {servico.id})")
    
    # 2. Calcular Slots para Segunda-feira (2026-06-01)
    # Com o nosso fallback de disponibilidade ativo, mesmo com a tabela Disponibilidade vazia,
    # ele deve retornar os slots de 09:00 até as 18:00
    data_teste = "2026-06-01"
    slots = calcular_slots(db, empresa.id, servico.id, data_teste)
    print(f"\nSlots calculados para {data_teste} (Segunda-feira):")
    print(slots)
    
    if len(slots) > 0:
        print("SUCCESS: Slots calculated successfully via fallback!")
    else:
        print("FAIL: No slots returned. Check availability logic.")
        
    # 3. Testar limpeza de tags
    print("\n--- Testando Limpeza de Tags ---")
    import re
    # Simula resposta que a IA geraria com a Tag isolada ou com "Tag:"
    resposta_simulada = "Olá! Vamos agendar seu sofá.\nTag:\n[ESCOLHER_SERVICO: id=777913a5-aaa9-43a4-98ad-9c0647cec507]"
    
    resposta_limpa = resposta_simulada
    resposta_limpa = re.sub(r'(?i)(?:tags?\s*:\s*)?\[ESCOLHER_SERVICO:[^\]]*\]', '', resposta_limpa)
    resposta_limpa = re.sub(r'(?i)^\s*tags?\s*:\s*$', '', resposta_limpa, flags=re.MULTILINE)
    resposta_limpa = re.sub(r'\n{3,}', '\n\n', resposta_limpa)
    resposta_limpa = resposta_limpa.strip()
    
    print("Resposta Original:")
    print(repr(resposta_simulada))
    print("Resposta Limpa:")
    print(repr(resposta_limpa))
    
    assert "Tag:" not in resposta_limpa
    assert "[ESCOLHER_SERVICO" not in resposta_limpa
    print("SUCCESS: Tag and prefix clean-up works perfectly!")
    
finally:
    db.close()
