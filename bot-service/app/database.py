import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversa(Base):
    __tablename__ = "conversas"
    id = Column(Integer, primary_key=True, index=True)
    telefone = Column(String, unique=True, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    mensagens = relationship("Mensagem", back_populates="conversa")

class Mensagem(Base):
    __tablename__ = "mensagens"
    id = Column(Integer, primary_key=True, index=True)
    conversa_id = Column(Integer, ForeignKey("conversas.id"))
    tipo = Column(String) # 'usuario' ou 'agente'
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversa = relationship("Conversa", back_populates="mensagens")

class Transbordo(Base):
    __tablename__ = "transbordo"
    id = Column(Integer, primary_key=True, index=True)
    telefone = Column(String, unique=True, index=True)
    status = Column(String, default="aguardando") # aguardando, pausado
    criado_em = Column(DateTime, default=datetime.utcnow)

# Criar as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def salvar_mensagem(conversa_id, tipo, mensagem_texto):
    db = get_db()
    nova_mensagem = Mensagem(conversa_id=conversa_id, tipo=tipo, mensagem=mensagem_texto)
    db.add(nova_mensagem)
    db.commit()

def obter_conversa(telefone):
    db = get_db()
    conversa = db.query(Conversa).filter(Conversa.telefone == telefone).first()
    if conversa:
        return conversa.id
    
    nova_conversa = Conversa(telefone=telefone)
    db.add(nova_conversa)
    db.commit()
    db.refresh(nova_conversa)
    return nova_conversa.id

def listar_conversas_com_mensagens():
    db = get_db()
    conversas = db.query(Conversa).order_by(Conversa.criado_em.desc()).all()
    resultado = []
    for conv in conversas:
        resultado.append({
            "id": conv.id,
            "telefone": conv.telefone,
            "criado_em": conv.criado_em,
            "mensagens": [
                {"tipo": m.tipo, "mensagem": m.mensagem, "timestamp": m.timestamp}
                for m in conv.mensagens
            ]
        })
    return resultado

# ── Funções de transbordo ──────────────────────────────────────────────────────

def obter_status_transbordo(telefone):
    db = get_db()
    transbordo = db.query(Transbordo).filter(Transbordo.telefone == telefone).first()
    return transbordo.status if transbordo else None

def marcar_aguardando_confirmacao(telefone):
    db = get_db()
    transbordo = db.query(Transbordo).filter(Transbordo.telefone == telefone).first()
    if transbordo:
        transbordo.status = "aguardando"
        transbordo.criado_em = datetime.utcnow()
    else:
        novo = Transbordo(telefone=telefone, status="aguardando")
        db.add(novo)
    db.commit()

def marcar_pausado(telefone):
    db = get_db()
    transbordo = db.query(Transbordo).filter(Transbordo.telefone == telefone).first()
    if transbordo:
        transbordo.status = "pausado"
        transbordo.criado_em = datetime.utcnow()
    else:
        novo = Transbordo(telefone=telefone, status="pausado")
        db.add(novo)
    db.commit()

def limpar_transbordo(telefone):
    db = get_db()
    transbordo = db.query(Transbordo).filter(Transbordo.telefone == telefone).first()
    if transbordo:
        db.delete(transbordo)
        db.commit()
