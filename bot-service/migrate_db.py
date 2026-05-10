import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    print("Iniciando migração do banco de dados...")
    
    # Converte URL para formato psycopg2 se necessário
    conn_url = DATABASE_URL
    if conn_url.startswith("postgres://"):
        conn_url = conn_url.replace("postgres://", "postgresql://", 1)

    try:
        conn = psycopg2.connect(conn_url)
        cur = conn.cursor()

        # Adiciona as colunas novas uma por uma (IF NOT EXISTS não funciona direto em ALTER TABLE, então usamos try/except ou verificamos)
        commands = [
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS slug VARCHAR UNIQUE",
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS valor_mensalidade FLOAT DEFAULT 0.0",
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS data_expiracao_teste TIMESTAMP",
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS cupom_vendedor VARCHAR",
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS evolution_instance VARCHAR UNIQUE"
        ]

        for cmd in commands:
            try:
                cur.execute(cmd)
                print(f"Executado: {cmd}")
            except Exception as e:
                print(f"Aviso ao executar {cmd}: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migração concluída com sucesso!")

    except Exception as e:
        print(f"Erro fatal na migração: {e}")

if __name__ == "__main__":
    migrate()
