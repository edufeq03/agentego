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
    campanhas = relationship("Campanha", back_populates="empresa", cascade="all, delete-orphan")
    membros_academia = relationship("MembroAcademia", back_populates="empresa", cascade="all, delete-orphan")
    empresas_clientes = relationship("EmpresaCliente", back_populates="empresa", cascade="all, delete-orphan")
    obrigacoes_fiscais = relationship("ObrigacaoFiscal", back_populates="empresa", cascade="all, delete-orphan")
    documentos_legais = relationship("DocumentoLegal", back_populates="empresa", cascade="all, delete-orphan")
    comunicados = relationship("Comunicado", back_populates="empresa", cascade="all, delete-orphan")
    leads_seguro = relationship("LeadSeguro", back_populates="empresa", cascade="all, delete-orphan")
    clientes_agencia_viagens = relationship("ClienteAgenciaViagens", back_populates="empresa", cascade="all, delete-orphan")
    listas_transmissao = relationship("ListaTransmissao", back_populates="empresa", cascade="all, delete-orphan")

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

class CodigoRecuperacao(Base):
    __tablename__ = "codigos_recuperacao"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    codigo = Column(String, nullable=False)
    expira_em = Column(DateTime, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    usuario = relationship("Usuario")

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
    utm_source = Column(String(50), nullable=True)
    utm_campaign = Column(String(50), nullable=True)
    canal_entrada = Column(String(50), default='organico')
    dados_customizados = Column(JSONB, nullable=False, default=dict)
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

class Campanha(Base):
    __tablename__ = "campanhas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    codigo_ref = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    origem = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="campanhas")

class CampoCustomizado(Base):
    __tablename__ = "campos_customizados"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    chave = Column(String(50), nullable=False)
    label = Column(String(100), nullable=False)
    tipo = Column(String(30), default="texto") # texto, numero, booleano, opcao_unica
    obrigatorio = Column(Boolean, default=False)
    opcoes = Column(JSONB, nullable=True) # Ex: ["particular", "trabalho"]
    ordem = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    dependencias = Column(JSONB, nullable=True) # Ex: {"tipo_seguro": ["Carro", "Moto"]}
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")

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

class Cardapio(Base):
    __tablename__ = "cardapio"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    categoria = Column(String, nullable=False) # Lanches, Bebidas, Sobremesas, etc.
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    disponivel = Column(Boolean, default=True)
    ordem = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    numero_pedido = Column(Integer, primary_key=False, nullable=True) # Sequencial por empresa ou autoincremento
    modo = Column(String, nullable=False) # 'delivery', 'balcao', 'mesa'
    status = Column(String, default="aguardando") # aguardando, em_preparo, pronto, entregue, cancelado
    total = Column(Float, nullable=True)
    observacao = Column(Text, nullable=True)
    endereco = Column(Text, nullable=True)
    nome_balcao = Column(String, nullable=True)
    numero_mesa = Column(Integer, nullable=True)
    avaliacao_nota = Column(Integer, nullable=True)
    avaliacao_comentario = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

class FollowupDelivery(Base):
    __tablename__ = "followup_delivery"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String, nullable=False)
    agendado_para = Column(DateTime, nullable=False)
    status = Column(String, default="pendente") # pendente, enviado, avaliado
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    pedido = relationship("Pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    cardapio_id = Column(UUID(as_uuid=True), ForeignKey("cardapio.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String, nullable=False)
    preco_unit = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)
    observacao = Column(Text, nullable=True)

    pedido = relationship("Pedido", back_populates="itens")
    cardapio = relationship("Cardapio")

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(Text, default="")
    duracao_min = Column(Integer, nullable=False)
    preco = Column(Float, nullable=True)
    ativo = Column(Boolean, default=True)
    cor = Column(String, default="#3b82f6")
    ordem = Column(Integer, default=0)
    tem_variacao_caracteristica = Column(Boolean, default=False)
    caracteristicas = Column(JSONB, default=list, nullable=True)
    recorrencia_sugerida_dias = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")

class Disponibilidade(Base):
    __tablename__ = "disponibilidade"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    dia_semana = Column(Integer, nullable=True)
    data_especifica = Column(String(10), nullable=True)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    intervalo_min = Column(Integer, default=30)
    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa")

class Bloqueio(Base):
    __tablename__ = "bloqueios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    data = Column(String(10), nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    motivo = Column(Text, default="")

    empresa = relationship("Empresa")

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="SET NULL"), nullable=True)
    servico_nome = Column(String, nullable=False)
    servico_duracao = Column(Integer, nullable=False)
    data = Column(String(10), nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fim = Column(String(5), nullable=False)
    status = Column(String, default="pendente")
    observacao = Column(Text, default="")
    motivo_cancelamento = Column(Text, default="")
    endereco = Column(Text, default="")
    lembrete_cliente_enviado = Column(Boolean, default=False)
    lembrete_profissional_enviado = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")
    itens = relationship("ItemAgendamento", back_populates="agendamento", cascade="all, delete-orphan")

class ItemAgendamento(Base):
    __tablename__ = "itens_agendamento"
    id = Column(Integer, primary_key=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="SET NULL"), nullable=True)
    servico_nome = Column(String, nullable=False)
    duracao_min = Column(Integer, nullable=False)
    preco = Column(Float, nullable=True)

    agendamento = relationship("Agendamento", back_populates="itens")
    servico = relationship("Servico")

class ListaEspera(Base):
    __tablename__ = "lista_espera"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    data = Column(String(10), nullable=False)
    data_flexivel = Column(Boolean, default=False)
    posicao = Column(Integer, nullable=False)
    status = Column(String, default="aguardando") # aguardando | notificado | confirmado | expirado
    notificado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")

class SerieRecorrencia(Base):
    __tablename__ = "series_recorrencia"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    intervalo_dias = Column(Integer, nullable=False)
    ultimo_agendamento = Column(String(10), nullable=False)
    proximo_sugerido = Column(String(10), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa")
    lead = relationship("Lead")
    servico = relationship("Servico")

class EstadoAuxiliar(Base):
    __tablename__ = "estado_auxiliar"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    estado_json = Column(Text, nullable=False, default="{}")
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa")


# ─── Nicho: Agência de Viagens ────────────────────────────────────────────────

class ClienteAgenciaViagens(Base):
    """Clientes específicos do nicho Agência de Viagens.
    Criados automaticamente ao primeiro contato via WhatsApp (pushName)."""
    __tablename__ = "clientes_agencia_viagens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    canal_entrada = Column(String, default="whatsapp")  # whatsapp, manual, csv
    destinos_interesse = Column(JSONB, default=list)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="clientes_agencia_viagens")
    lead = relationship("Lead")


# ─── Módulo Independente: Listas de Transmissão ───────────────────────────────

class ListaTransmissao(Base):
    """Lista nomeada de transmissão. Módulo independente aplicável a qualquer nicho."""
    __tablename__ = "listas_transmissao"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="listas_transmissao")
    contatos = relationship("ListaTransmissaoContato", back_populates="lista", cascade="all, delete-orphan")
    disparos = relationship("DisparoLista", back_populates="lista", cascade="all, delete-orphan")


class ListaTransmissaoContato(Base):
    """Contato pertencente a uma lista de transmissão."""
    __tablename__ = "listas_transmissao_contatos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lista_id = Column(UUID(as_uuid=True), ForeignKey("listas_transmissao.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String, nullable=True)
    telefone = Column(String, nullable=False)
    adicionado_em = Column(DateTime, default=datetime.utcnow)

    lista = relationship("ListaTransmissao", back_populates="contatos")


class DisparoLista(Base):
    """Registro de um disparo de mensagem para uma lista de transmissão."""
    __tablename__ = "disparos_lista"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lista_id = Column(UUID(as_uuid=True), ForeignKey("listas_transmissao.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    mensagem = Column(Text, nullable=False)
    imagem_url = Column(Text, nullable=True)
    status = Column(String, default="pendente")  # pendente, enviando, enviado, erro
    total_contatos = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    data_programada = Column(DateTime, nullable=True)
    enviado_em = Column(DateTime, nullable=True)

    lista = relationship("ListaTransmissao", back_populates="disparos")

# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        
        # Migração manual para adicionar colunas novas em tabelas existentes
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS etapas_funil JSONB DEFAULT \'["novo", "curioso", "interessado", "agendado"]\''))
            conn.execute(text('ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS etapas_funil JSONB DEFAULT \'["novo", "curioso", "interessado", "agendado"]\''))
            conn.execute(text('ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT \'client\''))
            conn.execute(text('ALTER TABLE disparos_lista ADD COLUMN IF NOT EXISTS data_programada TIMESTAMP'))
            
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
            
            # Migração de UTM e Campanhas para Leads
            conn.execute(text('ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_source VARCHAR(50)'))
            conn.execute(text('ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(50)'))
            conn.execute(text('ALTER TABLE leads ADD COLUMN IF NOT EXISTS canal_entrada VARCHAR(50) DEFAULT \'organico\''))
            
            # Tabela de Campanhas de Marketing
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS campanhas (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    codigo_ref VARCHAR(50) UNIQUE NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    origem VARCHAR(50) NOT NULL,
                    descricao TEXT,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            conn.execute(text('ALTER TABLE campanhas ADD COLUMN IF NOT EXISTS descricao TEXT'))
            
            # Migração para Comunicados (Imagem)
            conn.execute(text('ALTER TABLE comunicados ADD COLUMN IF NOT EXISTS imagem_url TEXT'))
            
            # Novas colunas e tabelas para Triagem Dinâmica (SaaS Global)
            conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS dados_customizados JSONB NOT NULL DEFAULT '{}'::jsonb"))
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS campos_customizados (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    chave VARCHAR(50) NOT NULL,
                    label VARCHAR(100) NOT NULL,
                    tipo VARCHAR(30) DEFAULT 'texto',
                    obrigatorio BOOLEAN DEFAULT FALSE,
                    opcoes JSONB,
                    ordem INTEGER DEFAULT 0,
                    ativo BOOLEAN DEFAULT TRUE,
                    dependencias JSONB,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            conn.execute(text('ALTER TABLE campos_customizados ADD COLUMN IF NOT EXISTS dependencias JSONB'))
            
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

            # Migração de campos no Pedido e tabela FollowupDelivery
            conn.execute(text('ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS avaliacao_nota INTEGER'))
            conn.execute(text('ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS avaliacao_comentario TEXT'))
            
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS followup_delivery (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    pedido_id UUID REFERENCES pedidos(id) ON DELETE CASCADE,
                    telefone VARCHAR NOT NULL,
                    agendado_para TIMESTAMP NOT NULL,
                    status VARCHAR DEFAULT 'pendente',
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))
            
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

            # Tabelas do Nicho Lanchonete
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS cardapio (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    categoria VARCHAR(100) NOT NULL,
                    nome VARCHAR(200) NOT NULL,
                    descricao TEXT,
                    preco DECIMAL(8,2) NOT NULL,
                    disponivel BOOLEAN DEFAULT TRUE,
                    ordem INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS pedidos (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
                    numero_pedido SERIAL,
                    modo VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'aguardando',
                    total DECIMAL(8,2),
                    observacao TEXT,
                    endereco TEXT,
                    nome_balcao VARCHAR(200),
                    numero_mesa INTEGER,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS itens_pedido (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    pedido_id UUID REFERENCES pedidos(id) ON DELETE CASCADE,
                    cardapio_id UUID REFERENCES cardapio(id) ON DELETE SET NULL,
                    nome VARCHAR(200) NOT NULL,
                    preco_unit DECIMAL(8,2) NOT NULL,
                    quantidade INTEGER NOT NULL,
                    observacao TEXT
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS servicos (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    nome VARCHAR(200) NOT NULL,
                    descricao TEXT DEFAULT '',
                    duracao_min INTEGER NOT NULL,
                    preco REAL,
                    ativo BOOLEAN DEFAULT TRUE,
                    cor VARCHAR(20) DEFAULT '#3b82f6',
                    ordem INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS disponibilidade (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    dia_semana INTEGER,
                    data_especifica VARCHAR(10),
                    hora_inicio VARCHAR(5) NOT NULL,
                    hora_fim VARCHAR(5) NOT NULL,
                    intervalo_min INTEGER DEFAULT 30,
                    ativo BOOLEAN DEFAULT TRUE,
                    UNIQUE(empresa_id, dia_semana, data_especifica)
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS bloqueios (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    data VARCHAR(10) NOT NULL,
                    hora_inicio VARCHAR(5) NOT NULL,
                    hora_fim VARCHAR(5) NOT NULL,
                    motivo TEXT DEFAULT ''
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS agendamentos (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
                    servico_id UUID REFERENCES servicos(id) ON DELETE SET NULL,
                    servico_nome VARCHAR(200) NOT NULL,
                    servico_duracao INTEGER NOT NULL,
                    data VARCHAR(10) NOT NULL,
                    hora_inicio VARCHAR(5) NOT NULL,
                    hora_fim VARCHAR(5) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pendente',
                    observacao TEXT DEFAULT '',
                    motivo_cancelamento TEXT DEFAULT '',
                    endereco TEXT DEFAULT '',
                    lembrete_cliente_enviado BOOLEAN DEFAULT FALSE,
                    lembrete_profissional_enviado BOOLEAN DEFAULT FALSE,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            # Migração: adiciona coluna endereco caso não exista
            conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS endereco TEXT DEFAULT ''"))

            # Criar tabela de estado_auxiliar
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS estado_auxiliar (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID UNIQUE NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    estado_json TEXT NOT NULL DEFAULT '{}',
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            # Tabelas do Nicho Beleza
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS itens_agendamento (
                    id SERIAL PRIMARY KEY,
                    agendamento_id INTEGER NOT NULL REFERENCES agendamentos(id) ON DELETE CASCADE,
                    servico_id UUID REFERENCES servicos(id) ON DELETE SET NULL,
                    servico_nome VARCHAR(200) NOT NULL,
                    duracao_min INTEGER NOT NULL,
                    preco REAL
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS lista_espera (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
                    servico_id UUID REFERENCES servicos(id) ON DELETE CASCADE,
                    data VARCHAR(10) NOT NULL,
                    data_flexivel BOOLEAN DEFAULT FALSE,
                    posicao INTEGER NOT NULL,
                    status VARCHAR(50) DEFAULT 'aguardando',
                    notificado_em TIMESTAMP,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS series_recorrencia (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
                    servico_id UUID REFERENCES servicos(id) ON DELETE CASCADE,
                    intervalo_dias INTEGER NOT NULL,
                    ultimo_agendamento VARCHAR(10) NOT NULL,
                    proximo_sugerido VARCHAR(10) NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text("ALTER TABLE servicos ADD COLUMN IF NOT EXISTS tem_variacao_caracteristica BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE servicos ADD COLUMN IF NOT EXISTS caracteristicas JSONB DEFAULT '[]'::jsonb"))
            conn.execute(text("ALTER TABLE servicos ADD COLUMN IF NOT EXISTS recorrencia_sugerida_dias INTEGER DEFAULT 0"))

            # ── Nicho: Agência de Viagens ──────────────────────────────────────────
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS clientes_agencia_viagens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
                    nome VARCHAR NOT NULL,
                    telefone VARCHAR NOT NULL,
                    email VARCHAR,
                    canal_entrada VARCHAR DEFAULT \'whatsapp\',
                    destinos_interesse JSONB DEFAULT \'[]\',
                    observacoes TEXT,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    atualizado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            # ── Módulo: Listas de Transmissão ──────────────────────────────────────
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS listas_transmissao (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    nome VARCHAR NOT NULL,
                    descricao TEXT,
                    criado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS listas_transmissao_contatos (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lista_id UUID REFERENCES listas_transmissao(id) ON DELETE CASCADE,
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    nome VARCHAR,
                    telefone VARCHAR NOT NULL,
                    adicionado_em TIMESTAMP DEFAULT NOW()
                )
            '''))

            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS disparos_lista (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    lista_id UUID REFERENCES listas_transmissao(id) ON DELETE CASCADE,
                    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
                    mensagem TEXT NOT NULL,
                    imagem_url TEXT,
                    status VARCHAR DEFAULT \'pendente\',
                    total_contatos INTEGER DEFAULT 0,
                    enviados INTEGER DEFAULT 0,
                    erros INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    data_programada TIMESTAMP,
                    enviado_em TIMESTAMP
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
