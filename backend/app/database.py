import os
import uuid
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# --- Fachada de Modelos ---
# Importando tudo de app.models para manter retrocompatibilidade
from app.models import *

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
            conn.execute(text('ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS pagamento_status VARCHAR DEFAULT \'pendente\''))
            
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
