import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuração da conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/atendimento")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_configs(db):
    print("Iniciando auditoria e migração de configurações...")
    
    # Busca todas as configurações atuais
    result = db.execute(text("SELECT id, empresa_id, config FROM configuracoes")).fetchall()
    
    updates_count = 0
    
    for row in result:
        config_id = row[0]
        empresa_id = row[1]
        config_data = row[2] or {}
        
        # Garante que config_data seja um dicionário
        if isinstance(config_data, str):
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError:
                config_data = {}
                
        needs_update = False
        
        # =====================================================================
        # BLOCO DE REGRAS DE MIGRAÇÃO
        # Adicione novas chaves padrão aqui no futuro para sincronizar templates
        # =====================================================================
        
        # 1. Configurações de Voz (TTS)
        if "tts_enabled" not in config_data:
            config_data["tts_enabled"] = True
            needs_update = True
            
        if "tts_always" not in config_data:
            config_data["tts_always"] = False
            needs_update = True
            
        if "provedor_tts" not in config_data:
            config_data["provedor_tts"] = "openai"
            needs_update = True
            
        if "tts_voice" not in config_data:
            config_data["tts_voice"] = "nova"
            needs_update = True
            
        # =====================================================================
        
        # Se houve alguma alteração, salva de volta no banco
        if needs_update:
            # Em PostgreSQL, precisamos garantir que o JSON/JSONB seja inserido corretamente.
            # O cast AS JSONB resolve problemas de tipagem da query.
            update_stmt = text(
                "UPDATE configuracoes SET config = CAST(:config_json AS JSONB) WHERE id = :id"
            )
            
            db.execute(update_stmt, {
                "config_json": json.dumps(config_data), 
                "id": config_id
            })
            updates_count += 1
            print(f"[+] Empresa {empresa_id} atualizada com novas configurações padrão.")
            
    # Efetiva as transações no banco
    db.commit()
    print(f"\nMigração concluída com sucesso! {updates_count} empresas foram atualizadas.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        migrate_configs(db)
    except Exception as e:
        print(f"Erro inesperado durante a migração: {e}")
        db.rollback()
    finally:
        db.close()
