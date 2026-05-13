from app.database import SessionLocal, Empresa, Configuracao
import json

def check_config():
    db = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        for e in empresas:
            config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == e.id).first()
            config_data = config_obj.config if config_obj else {}
            print(f"Empresa: {e.nome} (Instância: {e.evolution_instance})")
            print(f"Config: {json.dumps(config_data, indent=2)}")
            print("-" * 20)
    finally:
        db.close()

if __name__ == "__main__":
    check_config()
