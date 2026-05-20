import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
import logging
logger = logging.getLogger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não definida. Abortando.")
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
    nicho = Column(String, default="generico")
    
    # Relacionamentos
    configuracoes = relationship("Configuracao", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="empresa", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    mensagens = relationship("Mensagem", back_populates="empresa", cascade="all, delete-orphan")
    eventos = relationship("Evento", back_populates="empresa", cascade="all, delete-orphan")
    transbordos = relationship("Transbordo", back_populates="empresa", cascade="all, delete-orphan")
    membros_academia = relationship("MembroAcademia", back_populates="empresa", cascade="all, delete-orphan")
    empresas_clientes = relationship("EmpresaCliente", back_populates="empresa", cascade="all, delete-orphan")
    obrigacoes_fiscais = relationship("ObrigacaoFiscal", back_populates="empresa", cascade="all, delete-orphan")
    documentos_legais = relationship("DocumentoLegal", back_populates="empresa", cascade="all, delete-orphan")
    comunicados = relationship("Comunicado", back_populates="empresa", cascade="all, delete-orphan")
    leads_seguro = relationship("LeadSeguro", back_populates="empresa", cascade="all, delete-orphan")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_nicho = Column(String, unique=True, nullable=False)
    prompt_sistema = Column(Text, nullable=False)
    tom_voz = Column(Text, nullable=True)
    missao = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    etapas_funil = Column(JSONB, default=["novo", "curioso", "interessado", "agendado"])
    nicho = Column(String, default="generico")
    criado_em = Column(DateTime, default=datetime.utcnow)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    role = Column(String, default="client") # "client" ou "admin" (franqueador)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="usuarios")

class Configuracao(Base):
    __tablename__ = "configuracoes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True)
    config = Column(JSONB, nullable=False, default=dict)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="configuracoes")

class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    stage = Column(String, default='novo') # novo, curioso, interessado, quente, agendado, perdido
    visit_offer_made = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="leads")
    mensagens = relationship("Mensagem", back_populates="lead", cascade="all, delete-orphan")
    seguro = relationship("LeadSeguro", back_populates="lead", uselist=False, cascade="all, delete-orphan")

class Mensagem(Base):
    __tablename__ = "mensagens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
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
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    tipo = Column(String, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict) # 'metadata' é reservado em sqlalchemy
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="eventos")
    lead = relationship("Lead")

class Transbordo(Base):
    __tablename__ = "transbordo"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    status = Column(String, default="aguardando") # aguardando, pausado
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="transbordos")

class MembroAcademia(Base):
    __tablename__ = "membros_academia"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    plano_nome = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    aviso_7_dias_enviado = Column(Boolean, default=False)
    aviso_3_dias_enviado = Column(Boolean, default=False)
    aviso_vencido_enviado = Column(Boolean, default=False)
    importado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")

class EmpresaCliente(Base):
    __tablename__ = "empresas_clientes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome_empresa = Column(String, nullable=False)
    cnpj = Column(String, nullable=True)
    regime_tributario = Column(String, nullable=True)
    contato_nome = Column(String, nullable=True)
    contato_telefone = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="empresas_clientes")

class ObrigacaoFiscal(Base):
    __tablename__ = "obrigacoes_fiscais"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    empresa_cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas_clientes.id"), nullable=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    prazo = Column(DateTime, nullable=False)
    status = Column(String, default="pendente")
    aviso_enviado = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="obrigacoes_fiscais")

class DocumentoLegal(Base):
    __tablename__ = "documentos_legais"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String, nullable=False)
    categoria = Column(String, nullable=True)
    conteudo = Column(Text, nullable=False)
    fonte = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    empresa = relationship("Empresa", back_populates="documentos_legais")

class Comunicado(Base):
    __tablename__ = "comunicados"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    mensagem = Column(Text, nullable=False)
    imagem_url = Column(Text, nullable=True)
    data_programada = Column(DateTime, nullable=True)
    status = Column(String, default="pendente") # rascunho, pendente, enviando, enviado, erro
    total_membros = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    enviado_em = Column(DateTime, nullable=True)

    empresa = relationship("Empresa")

class ComunicadoLog(Base):
    __tablename__ = "comunicado_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comunicado_id = Column(UUID(as_uuid=True), ForeignKey("comunicados.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    status = Column(String, nullable=False) # sucesso, erro
    erro = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    comunicado = relationship("Comunicado")

class LeadSeguro(Base):
    __tablename__ = "leads_seguro"
    id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String(20), nullable=False)
    nome_contato = Column(String(200), nullable=True)
    nome_segurado = Column(String(200), nullable=True)
    relacao_segurado = Column(String(50), nullable=True) # proprio, conjuge, filho, pai, outro
    
    tipo_seguro = Column(String(30), nullable=True) # saude, odontologico, auto, moto, residencial, empresarial, outro
    produto_especifico = Column(String(100), nullable=True)
    
    idade_segurado = Column(Integer, nullable=True)
    tem_cnpj = Column(Boolean, nullable=True)
    e_mei = Column(Boolean, nullable=True)
    tem_plano_anterior = Column(Boolean, nullable=True)
    plano_anterior_nome = Column(String(100), nullable=True)
    mais_de_6_meses = Column(Boolean, nullable=True)
    regiao = Column(String(200), nullable=True)
    hospitais_preferidos = Column(Text, nullable=True)
    
    marca_modelo = Column(String(100), nullable=True)
    ano_fabricacao = Column(Integer, nullable=True)
    ano_modelo = Column(Integer, nullable=True)
    placa = Column(String(10), nullable=True)
    cep_pernoite = Column(String(10), nullable=True)
    uso_veiculo = Column(String(30), nullable=True) # particular, trabalho, aplicativo
    tem_garagem = Column(Boolean, nullable=True)
    condutor_principal = Column(String(200), nullable=True)
    idade_condutor = Column(Integer, nullable=True)
    bonus_classe = Column(Integer, nullable=True)
    
    tipo_imovel = Column(String(30), nullable=True) # casa, apartamento, comercial
    cep_imovel = Column(String(10), nullable=True)
    metragem = Column(Integer, nullable=True)
    imovel_proprio = Column(Boolean, nullable=True)
    
    docs_recebidos = Column(JSONB, default=list) # [{"tipo": "cnh", "recebido_em": "..."}]
    docs_pendentes = Column(JSONB, default=list)
    
    stage = Column(String(30), default='novo') # novo, primeiro_contato, coletando_dados, aguardando_documentos, em_cotacao, proposta_enviada, negociando, fechado, renovacao_pendente, perdido
    canal_entrada = Column(String(20), default='organico') # template, organico
    template_raw = Column(Text, nullable=True)
    resumo_ia = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    
    seguradora_escolhida = Column(String(100), nullable=True)
    valor_proposta = Column(Float, nullable=True)
    data_proposta_enviada = Column(DateTime, nullable=True)
    data_vencimento_apolice = Column(DateTime, nullable=True)
    numero_apolice = Column(String(100), nullable=True)
    
    ultimo_followup_em = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0)
    motivo_perda = Column(String(200), nullable=True)
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="leads_seguro")
    lead = relationship("Lead", back_populates="seguro")

class DocumentoSeguro(Base):
    __tablename__ = "documentos_seguro"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads_seguro.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    tipo = Column(String(30), nullable=False) # cnh, crlv, rg, cpf, comprovante_residencia, apolice_anterior, fatura_anterior, foto_veiculo, laudo_medico, outro
    arquivo_nome = Column(String(300), nullable=True)
    arquivo_path = Column(String(500), nullable=True)
    arquivo_url = Column(String(500), nullable=True)
    mimetype = Column(String(100), nullable=True)
    ocr_processado = Column(Boolean, default=False)
    ocr_resultado = Column(JSONB, default=dict)
    ocr_confianca = Column(Float, nullable=True)
    recebido_em = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("LeadSeguro")
    empresa = relationship("Empresa")

class FollowupSeguro(Base):
    __tablename__ = "followups_seguro"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads_seguro.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    tipo = Column(String(30), nullable=True) # manual, automatico_sugestao, automatico_enviado
    mensagem = Column(Text, nullable=False)
    enviado_em = Column(DateTime, default=datetime.utcnow)
    resultado = Column(String(30), default='pendente') # respondeu, ignorou, pendente
    
    lead = relationship("LeadSeguro")
    empresa = relationship("Empresa")

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
            
            # Nicho e Novas Tabelas
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS nicho VARCHAR DEFAULT \'generico\''))
            conn.execute(text('ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS nicho VARCHAR DEFAULT \'generico\''))
            
            # Migração para Comunicados (Imagem)
            conn.execute(text('ALTER TABLE comunicados ADD COLUMN IF NOT EXISTS imagem_url TEXT'))
            
            # Garantir ON DELETE CASCADE em tabelas existentes
            try:
                conn.execute(text('ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE usuarios ADD CONSTRAINT usuarios_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))
                
                conn.execute(text('ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE leads ADD CONSTRAINT leads_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))
                
                conn.execute(text('ALTER TABLE mensagens DROP CONSTRAINT IF EXISTS mensagens_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE mensagens ADD CONSTRAINT mensagens_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))
                
                conn.execute(text('ALTER TABLE eventos DROP CONSTRAINT IF EXISTS eventos_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE eventos ADD CONSTRAINT eventos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))
                
                conn.execute(text('ALTER TABLE transbordo DROP CONSTRAINT IF EXISTS transbordo_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE transbordo ADD CONSTRAINT transbordo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE configuracoes DROP CONSTRAINT IF EXISTS configuracoes_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE configuracoes ADD CONSTRAINT configuracoes_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE membros_academia DROP CONSTRAINT IF EXISTS membros_academia_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE membros_academia ADD CONSTRAINT membros_academia_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE empresas_clientes DROP CONSTRAINT IF EXISTS empresas_clientes_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE empresas_clientes ADD CONSTRAINT empresas_clientes_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE obrigacoes_fiscais DROP CONSTRAINT IF EXISTS obrigacoes_fiscais_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE obrigacoes_fiscais ADD CONSTRAINT obrigacoes_fiscais_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE documentos_legais DROP CONSTRAINT IF EXISTS documentos_legais_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE documentos_legais ADD CONSTRAINT documentos_legais_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))

                conn.execute(text('ALTER TABLE comunicados DROP CONSTRAINT IF EXISTS comunicados_empresa_id_fkey'))
                conn.execute(text('ALTER TABLE comunicados ADD CONSTRAINT comunicados_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE'))
            except Exception as e:
                logger.warning(f"Erro ao aplicar migração de cascade (pode já existir): {e}")
            
            # Tabelas específicas (manualmente se create_all falhar por algum motivo)
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS membros_academia (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    nome VARCHAR NOT NULL,
                    telefone VARCHAR NOT NULL,
                    data_vencimento TIMESTAMP NOT NULL,
                    plano_nome VARCHAR,
                    ativo BOOLEAN DEFAULT TRUE,
                    aviso_7_dias_enviado BOOLEAN DEFAULT FALSE,
                    aviso_3_dias_enviado BOOLEAN DEFAULT FALSE,
                    aviso_vencido_enviado BOOLEAN DEFAULT FALSE,
                    importado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS empresas_clientes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    nome_empresa VARCHAR NOT NULL,
                    cnpj VARCHAR,
                    regime_tributario VARCHAR,
                    contato_nome VARCHAR,
                    contato_telefone VARCHAR,
                    ativo BOOLEAN DEFAULT TRUE,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS obrigacoes_fiscais (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    empresa_cliente_id UUID REFERENCES empresas_clientes(id) ON DELETE SET NULL,
                    titulo VARCHAR NOT NULL,
                    descricao TEXT,
                    prazo TIMESTAMP NOT NULL,
                    status VARCHAR DEFAULT 'pendente',
                    aviso_enviado BOOLEAN DEFAULT FALSE,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS documentos_legais (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    titulo VARCHAR NOT NULL,
                    categoria VARCHAR,
                    conteudo TEXT NOT NULL,
                    fonte VARCHAR,
                    ativo BOOLEAN DEFAULT TRUE,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS comunicados (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    mensagem TEXT NOT NULL,
                    imagem_url TEXT,
                    data_programada TIMESTAMP,
                    status VARCHAR DEFAULT 'pendente',
                    total_membros INTEGER DEFAULT 0,
                    enviados INTEGER DEFAULT 0,
                    erros INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    enviado_em TIMESTAMP
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS comunicado_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    comunicado_id UUID REFERENCES comunicados(id) ON DELETE CASCADE,
                    telefone VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    erro TEXT,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS leads_seguro (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    telefone VARCHAR(20) NOT NULL,
                    nome_contato VARCHAR(200),
                    nome_segurado VARCHAR(200),
                    relacao_segurado VARCHAR(50),
                    tipo_seguro VARCHAR(30),
                    produto_especifico VARCHAR(100),
                    idade_segurado INTEGER,
                    tem_cnpj BOOLEAN,
                    e_mei BOOLEAN,
                    tem_plano_anterior BOOLEAN,
                    plano_anterior_nome VARCHAR(100),
                    mais_de_6_meses BOOLEAN,
                    regiao VARCHAR(200),
                    hospitais_preferidos TEXT,
                    marca_modelo VARCHAR(100),
                    ano_fabricacao INTEGER,
                    ano_modelo INTEGER,
                    placa VARCHAR(10),
                    cep_pernoite VARCHAR(10),
                    uso_veiculo VARCHAR(30),
                    tem_garagem BOOLEAN,
                    condutor_principal VARCHAR(200),
                    idade_condutor INTEGER,
                    bonus_classe INTEGER,
                    tipo_imovel VARCHAR(30),
                    cep_imovel VARCHAR(10),
                    metragem INTEGER,
                    imovel_proprio BOOLEAN,
                    docs_recebidos JSONB DEFAULT '[]',
                    docs_pendentes JSONB DEFAULT '[]',
                    stage VARCHAR(30) DEFAULT 'novo',
                    canal_entrada VARCHAR(20) DEFAULT 'organico',
                    template_raw TEXT,
                    resumo_ia TEXT,
                    observacoes TEXT,
                    seguradora_escolhida VARCHAR(100),
                    valor_proposta DECIMAL(10,2),
                    data_proposta_enviada TIMESTAMP,
                    data_vencimento_apolice TIMESTAMP,
                    numero_apolice VARCHAR(100),
                    ultimo_followup_em TIMESTAMP,
                    followup_count INTEGER DEFAULT 0,
                    motivo_perda VARCHAR(200),
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS documentos_seguro (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lead_id UUID REFERENCES leads_seguro(id) ON DELETE CASCADE,
                    empresa_id UUID REFERENCES empresas(id),
                    tipo VARCHAR(30) NOT NULL,
                    arquivo_nome VARCHAR(300),
                    arquivo_path VARCHAR(500),
                    arquivo_url VARCHAR(500),
                    mimetype VARCHAR(100),
                    ocr_processado BOOLEAN DEFAULT FALSE,
                    ocr_resultado JSONB DEFAULT '{}',
                    ocr_confianca FLOAT,
                    recebido_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS followups_seguro (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lead_id UUID REFERENCES leads_seguro(id) ON DELETE CASCADE,
                    empresa_id UUID REFERENCES empresas(id),
                    tipo VARCHAR(30),
                    mensagem TEXT,
                    enviado_em TIMESTAMP DEFAULT NOW(),
                    resultado VARCHAR(30) DEFAULT 'pendente'
                )
            '''))

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
