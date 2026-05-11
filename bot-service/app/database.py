import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atendimento")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    telefone_whatsapp = Column(String, unique=True, nullable=False)
    telefone_proprietario = Column(String, nullable=True)
    webhook_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    evolution_instance = Column(String, unique=True, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    valor_mensalidade = Column(Float, default=0.0)
    data_expiracao_teste = Column(DateTime, nullable=True)
    cupom_vendedor = Column(String, nullable=True)
    
    # Billing e Planos
    plano = Column(String, default="trial") # trial, starter, pro, ilimitado
    limite_conversas_mes = Column(Integer, default=100)
    conversas_mes_atual = Column(Integer, default=0)
    data_reset_contador = Column(DateTime, nullable=True)
    
    # Rastreamento interno de custos (tokens)
    tokens_input_mes = Column(Integer, default=0)
    tokens_output_mes = Column(Integer, default=0)
    
    data_criacao = Column(DateTime, server_default=func.now())
    etapas_funil = Column(JSONB, default=["novo", "curioso", "interessado", "agendado"])
    
    # Relacionamentos
    configuracoes = relationship("Configuracao", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="empresa", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    mensagens = relationship("Mensagem", back_populates="empresa", cascade="all, delete-orphan")
    eventos = relationship("Evento", back_populates="empresa", cascade="all, delete-orphan")
    transbordos = relationship("Transbordo", back_populates="empresa", cascade="all, delete-orphan")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_nicho = Column(String, unique=True, nullable=False)
    prompt_sistema = Column(Text, nullable=False)
    tom_voz = Column(Text, nullable=True)
    missao = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    etapas_funil = Column(JSONB, default=["novo", "curioso", "interessado", "agendado"])
    criado_em = Column(DateTime, default=datetime.utcnow)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    role = Column(String, default="client") # "client" ou "admin" (franqueador)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="usuarios")

class Configuracao(Base):
    __tablename__ = "configuracoes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, unique=True)
    config = Column(JSONB, nullable=False, default=dict)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="configuracoes")

class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    telefone = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    stage = Column(String, default='novo') # novo, curioso, interessado, quente, agendado, perdido
    visit_offer_made = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="leads")
    mensagens = relationship("Mensagem", back_populates="lead", cascade="all, delete-orphan")

class Mensagem(Base):
    __tablename__ = "mensagens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    tipo = Column(String, nullable=False) # 'usuario' ou 'agente'
    mensagem = Column(Text, nullable=False)
    intencao = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="mensagens")
    empresa = relationship("Empresa", back_populates="mensagens")

class Evento(Base):
    __tablename__ = "eventos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    tipo = Column(String, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict) # 'metadata' é reservado em sqlalchemy
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="eventos")
    lead = relationship("Lead")

class Transbordo(Base):
    __tablename__ = "transbordo"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    telefone = Column(String, nullable=False)
    status = Column(String, default="aguardando") # aguardando, pausado
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="transbordos")

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        
        # Migração manual para adicionar colunas novas em tabelas existentes
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS etapas_funil JSONB DEFAULT \'["novo", "curioso", "interessado", "agendado"]\''))
            conn.execute(text('ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS etapas_funil JSONB DEFAULT \'["novo", "curioso", "interessado", "agendado"]\''))
            conn.execute(text('ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT \'client\''))
            
            # Novas colunas de Billing
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS plano VARCHAR DEFAULT \'trial\''))
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS limite_conversas_mes INTEGER DEFAULT 100'))
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS conversas_mes_atual INTEGER DEFAULT 0'))
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS data_reset_contador TIMESTAMP'))
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS tokens_input_mes INTEGER DEFAULT 0'))
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS tokens_output_mes INTEGER DEFAULT 0'))
            
            conn.commit()
            
        print("Conexão com banco de dados estabelecida e migrações do SaaS concluídas.")
    except Exception as e:
        print(f"AVISO: Erro ao inicializar banco de dados: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
