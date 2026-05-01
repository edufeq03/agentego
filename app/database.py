import sqlite3
import os

# Garantir que o banco de dados fique na raiz do projeto, não na pasta app/
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conversas.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefone TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id INTEGER,
    tipo TEXT,
    mensagem TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transbordo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefone TEXT UNIQUE,
    status TEXT DEFAULT 'aguardando',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

def salvar_mensagem(conversa_id, tipo, mensagem):
    cursor.execute("""
        INSERT INTO mensagens (conversa_id, tipo, mensagem)
        VALUES (?, ?, ?)
    """, (conversa_id, tipo, mensagem))
    
    conn.commit()

def obter_conversa(telefone):
    cursor.execute("""
        SELECT id FROM conversas WHERE telefone = ?
    """, (telefone,))
    
    result = cursor.fetchone()

    if result:
        return result[0]
    
    cursor.execute("""
        INSERT INTO conversas (telefone) VALUES (?)
    """, (telefone,))
    
    conn.commit()
    
    return cursor.lastrowid

def listar_conversas_com_mensagens():
    cursor.execute("""
        SELECT id, telefone, criado_em FROM conversas ORDER BY criado_em DESC
    """)
    conversas = cursor.fetchall()
    
    resultado = []
    for conv in conversas:
        conv_id = conv[0]
        cursor.execute("""
            SELECT tipo, mensagem, timestamp FROM mensagens 
            WHERE conversa_id = ? ORDER BY timestamp ASC
        """, (conv_id,))
        mensagens = cursor.fetchall()
        
        resultado.append({
            "id": conv_id,
            "telefone": conv[1],
            "criado_em": conv[2],
            "mensagens": [{"tipo": m[0], "mensagem": m[1], "timestamp": m[2]} for m in mensagens]
        })
        
    return resultado

# ── Funções de transbordo ──────────────────────────────────────────────────────

def obter_status_transbordo(telefone):
    """Retorna o status de transbordo do número, ou None se não existir."""
    cursor.execute("SELECT status FROM transbordo WHERE telefone = ?", (telefone,))
    result = cursor.fetchone()
    return result[0] if result else None

def marcar_aguardando_confirmacao(telefone):
    """Rosana acabou de sugerir transbordo — aguardando resposta do cliente."""
    cursor.execute("""
        INSERT INTO transbordo (telefone, status) VALUES (?, 'aguardando')
        ON CONFLICT(telefone) DO UPDATE SET status = 'aguardando', criado_em = CURRENT_TIMESTAMP
    """, (telefone,))
    conn.commit()

def marcar_pausado(telefone):
    """Cliente confirmou — robô silenciado para este número."""
    cursor.execute("""
        INSERT INTO transbordo (telefone, status) VALUES (?, 'pausado')
        ON CONFLICT(telefone) DO UPDATE SET status = 'pausado', criado_em = CURRENT_TIMESTAMP
    """, (telefone,))
    conn.commit()

def limpar_transbordo(telefone):
    """Remove o bloqueio — robô volta a responder normalmente (uso manual/admin)."""
    cursor.execute("DELETE FROM transbordo WHERE telefone = ?", (telefone,))
    conn.commit()
