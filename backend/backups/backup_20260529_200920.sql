--
-- PostgreSQL database dump
--

\restrict MxGUnC4S7u1c4gdhBfnroWiiUBEk5TqLvgE5PGaZe8LMd37NV5PQBgIKrjl1usU

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agendamentos; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.agendamentos (
    id integer NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid,
    servico_id uuid,
    servico_nome character varying NOT NULL,
    servico_duracao integer NOT NULL,
    data character varying(10) NOT NULL,
    hora_inicio character varying(5) NOT NULL,
    hora_fim character varying(5) NOT NULL,
    status character varying,
    observacao text,
    motivo_cancelamento text,
    lembrete_cliente_enviado boolean,
    lembrete_profissional_enviado boolean,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone,
    endereco text DEFAULT ''::text
);


ALTER TABLE public.agendamentos OWNER TO "user";

--
-- Name: agendamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.agendamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.agendamentos_id_seq OWNER TO "user";

--
-- Name: agendamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.agendamentos_id_seq OWNED BY public.agendamentos.id;


--
-- Name: bloqueios; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.bloqueios (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    data character varying(10) NOT NULL,
    hora_inicio character varying(5) NOT NULL,
    hora_fim character varying(5) NOT NULL,
    motivo text
);


ALTER TABLE public.bloqueios OWNER TO "user";

--
-- Name: campanhas; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.campanhas (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    codigo_ref character varying(50) NOT NULL,
    nome character varying(100) NOT NULL,
    origem character varying(50) NOT NULL,
    criado_em timestamp without time zone,
    descricao text
);


ALTER TABLE public.campanhas OWNER TO "user";

--
-- Name: campos_customizados; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.campos_customizados (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    chave character varying(50) NOT NULL,
    label character varying(100) NOT NULL,
    tipo character varying(30),
    obrigatorio boolean,
    opcoes jsonb,
    ordem integer,
    ativo boolean,
    criado_em timestamp without time zone,
    dependencias jsonb
);


ALTER TABLE public.campos_customizados OWNER TO "user";

--
-- Name: cardapio; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.cardapio (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    categoria character varying NOT NULL,
    nome character varying NOT NULL,
    descricao text,
    preco double precision NOT NULL,
    disponivel boolean,
    ordem integer,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.cardapio OWNER TO "user";

--
-- Name: codigos_recuperacao; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.codigos_recuperacao (
    id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    codigo character varying NOT NULL,
    expira_em timestamp without time zone NOT NULL,
    criado_em timestamp without time zone
);


ALTER TABLE public.codigos_recuperacao OWNER TO "user";

--
-- Name: comunicado_logs; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.comunicado_logs (
    id uuid NOT NULL,
    comunicado_id uuid NOT NULL,
    telefone character varying NOT NULL,
    status character varying NOT NULL,
    erro text,
    criado_em timestamp without time zone
);


ALTER TABLE public.comunicado_logs OWNER TO "user";

--
-- Name: comunicados; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.comunicados (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    mensagem text NOT NULL,
    data_programada timestamp without time zone,
    status character varying,
    total_membros integer,
    enviados integer,
    erros integer,
    criado_em timestamp without time zone,
    enviado_em timestamp without time zone,
    imagem_url text
);


ALTER TABLE public.comunicados OWNER TO "user";

--
-- Name: configuracoes; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.configuracoes (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    config jsonb NOT NULL,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.configuracoes OWNER TO "user";

--
-- Name: disponibilidade; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.disponibilidade (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    dia_semana integer,
    data_especifica character varying(10),
    hora_inicio character varying(5) NOT NULL,
    hora_fim character varying(5) NOT NULL,
    intervalo_min integer,
    ativo boolean
);


ALTER TABLE public.disponibilidade OWNER TO "user";

--
-- Name: documentos_legais; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.documentos_legais (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    titulo character varying NOT NULL,
    categoria character varying,
    conteudo text NOT NULL,
    fonte character varying,
    ativo boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.documentos_legais OWNER TO "user";

--
-- Name: documentos_seguro; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.documentos_seguro (
    id uuid NOT NULL,
    lead_id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    tipo character varying(30) NOT NULL,
    arquivo_nome character varying(300),
    arquivo_path character varying(500),
    arquivo_url character varying(500),
    mimetype character varying(100),
    ocr_processado boolean,
    ocr_resultado jsonb,
    ocr_confianca double precision,
    recebido_em timestamp without time zone
);


ALTER TABLE public.documentos_seguro OWNER TO "user";

--
-- Name: empresas; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.empresas (
    id uuid NOT NULL,
    nome character varying NOT NULL,
    telefone_whatsapp character varying NOT NULL,
    telefone_proprietario character varying,
    webhook_token character varying NOT NULL,
    ativo boolean,
    criado_em timestamp without time zone,
    etapas_funil jsonb DEFAULT '["novo", "curioso", "interessado", "agendado"]'::jsonb,
    slug character varying,
    valor_mensalidade double precision DEFAULT 0.0,
    data_expiracao_teste timestamp without time zone,
    cupom_vendedor character varying,
    data_criacao timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    evolution_instance character varying,
    plano character varying DEFAULT 'trial'::character varying,
    limite_conversas_mes integer DEFAULT 100,
    conversas_mes_atual integer DEFAULT 0,
    data_reset_contador timestamp without time zone,
    tokens_input_mes integer DEFAULT 0,
    tokens_output_mes integer DEFAULT 0,
    nicho character varying DEFAULT 'generico'::character varying
);


ALTER TABLE public.empresas OWNER TO "user";

--
-- Name: empresas_clientes; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.empresas_clientes (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    nome_empresa character varying NOT NULL,
    cnpj character varying,
    regime_tributario character varying,
    contato_nome character varying,
    contato_telefone character varying,
    ativo boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.empresas_clientes OWNER TO "user";

--
-- Name: estado_auxiliar; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.estado_auxiliar (
    id integer NOT NULL,
    empresa_id uuid NOT NULL,
    estado_json text NOT NULL,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.estado_auxiliar OWNER TO "user";

--
-- Name: estado_auxiliar_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.estado_auxiliar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.estado_auxiliar_id_seq OWNER TO "user";

--
-- Name: estado_auxiliar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.estado_auxiliar_id_seq OWNED BY public.estado_auxiliar.id;


--
-- Name: eventos; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.eventos (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid,
    tipo character varying NOT NULL,
    metadata jsonb,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.eventos OWNER TO "user";

--
-- Name: followups_seguro; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.followups_seguro (
    id uuid NOT NULL,
    lead_id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    tipo character varying(30),
    mensagem text NOT NULL,
    enviado_em timestamp without time zone,
    resultado character varying(30)
);


ALTER TABLE public.followups_seguro OWNER TO "user";

--
-- Name: itens_agendamento; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.itens_agendamento (
    id integer NOT NULL,
    agendamento_id integer NOT NULL,
    servico_id uuid,
    servico_nome character varying NOT NULL,
    duracao_min integer NOT NULL,
    preco double precision
);


ALTER TABLE public.itens_agendamento OWNER TO "user";

--
-- Name: itens_agendamento_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.itens_agendamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.itens_agendamento_id_seq OWNER TO "user";

--
-- Name: itens_agendamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.itens_agendamento_id_seq OWNED BY public.itens_agendamento.id;


--
-- Name: itens_pedido; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.itens_pedido (
    id uuid NOT NULL,
    pedido_id uuid NOT NULL,
    cardapio_id uuid,
    nome character varying NOT NULL,
    preco_unit double precision NOT NULL,
    quantidade integer NOT NULL,
    observacao text
);


ALTER TABLE public.itens_pedido OWNER TO "user";

--
-- Name: leads; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.leads (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    telefone character varying NOT NULL,
    nome character varying,
    stage character varying,
    visit_offer_made boolean,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone,
    utm_source character varying(50),
    utm_campaign character varying(50),
    canal_entrada character varying(50) DEFAULT 'organico'::character varying,
    dados_customizados jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE public.leads OWNER TO "user";

--
-- Name: leads_seguro; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.leads_seguro (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    telefone character varying(20) NOT NULL,
    nome_contato character varying(200),
    nome_segurado character varying(200),
    relacao_segurado character varying(50),
    tipo_seguro character varying(30),
    produto_especifico character varying(100),
    idade_segurado integer,
    tem_cnpj boolean,
    e_mei boolean,
    tem_plano_anterior boolean,
    plano_anterior_nome character varying(100),
    mais_de_6_meses boolean,
    regiao character varying(200),
    hospitais_preferidos text,
    marca_modelo character varying(100),
    ano_fabricacao integer,
    ano_modelo integer,
    placa character varying(10),
    cep_pernoite character varying(10),
    uso_veiculo character varying(30),
    tem_garagem boolean,
    condutor_principal character varying(200),
    idade_condutor integer,
    bonus_classe integer,
    tipo_imovel character varying(30),
    cep_imovel character varying(10),
    metragem integer,
    imovel_proprio boolean,
    docs_recebidos jsonb,
    docs_pendentes jsonb,
    stage character varying(30),
    canal_entrada character varying(20),
    template_raw text,
    resumo_ia text,
    observacoes text,
    seguradora_escolhida character varying(100),
    valor_proposta double precision,
    data_proposta_enviada timestamp without time zone,
    data_vencimento_apolice timestamp without time zone,
    numero_apolice character varying(100),
    ultimo_followup_em timestamp without time zone,
    followup_count integer,
    motivo_perda character varying(200),
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.leads_seguro OWNER TO "user";

--
-- Name: lista_espera; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.lista_espera (
    id integer NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid NOT NULL,
    servico_id uuid NOT NULL,
    data character varying(10) NOT NULL,
    data_flexivel boolean,
    posicao integer NOT NULL,
    status character varying,
    notificado_em timestamp without time zone,
    criado_em timestamp without time zone
);


ALTER TABLE public.lista_espera OWNER TO "user";

--
-- Name: lista_espera_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.lista_espera_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lista_espera_id_seq OWNER TO "user";

--
-- Name: lista_espera_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.lista_espera_id_seq OWNED BY public.lista_espera.id;


--
-- Name: membros_academia; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.membros_academia (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    nome character varying NOT NULL,
    telefone character varying NOT NULL,
    data_vencimento timestamp without time zone NOT NULL,
    plano_nome character varying,
    ativo boolean,
    aviso_7_dias_enviado boolean,
    aviso_3_dias_enviado boolean,
    aviso_vencido_enviado boolean,
    importado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.membros_academia OWNER TO "user";

--
-- Name: mensagens; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.mensagens (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid NOT NULL,
    tipo character varying NOT NULL,
    mensagem text NOT NULL,
    intencao character varying,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.mensagens OWNER TO "user";

--
-- Name: obrigacoes_fiscais; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.obrigacoes_fiscais (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    empresa_cliente_id uuid,
    titulo character varying NOT NULL,
    descricao text,
    prazo timestamp without time zone NOT NULL,
    status character varying,
    aviso_enviado boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.obrigacoes_fiscais OWNER TO "user";

--
-- Name: pedidos; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pedidos (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid,
    numero_pedido integer,
    modo character varying NOT NULL,
    status character varying,
    total double precision,
    observacao text,
    endereco text,
    nome_balcao character varying,
    numero_mesa integer,
    criado_em timestamp without time zone,
    atualizado_em timestamp without time zone
);


ALTER TABLE public.pedidos OWNER TO "user";

--
-- Name: prompt_templates; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.prompt_templates (
    id uuid NOT NULL,
    nome_nicho character varying NOT NULL,
    prompt_sistema text NOT NULL,
    tom_voz text,
    missao text,
    objetivo text,
    etapas_funil jsonb,
    criado_em timestamp without time zone,
    nicho character varying DEFAULT 'generico'::character varying
);


ALTER TABLE public.prompt_templates OWNER TO "user";

--
-- Name: series_recorrencia; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.series_recorrencia (
    id integer NOT NULL,
    empresa_id uuid NOT NULL,
    lead_id uuid NOT NULL,
    servico_id uuid NOT NULL,
    intervalo_dias integer NOT NULL,
    ultimo_agendamento character varying(10) NOT NULL,
    proximo_sugerido character varying(10) NOT NULL,
    ativo boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.series_recorrencia OWNER TO "user";

--
-- Name: series_recorrencia_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.series_recorrencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_recorrencia_id_seq OWNER TO "user";

--
-- Name: series_recorrencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.series_recorrencia_id_seq OWNED BY public.series_recorrencia.id;


--
-- Name: servicos; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.servicos (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    nome character varying NOT NULL,
    descricao text,
    duracao_min integer NOT NULL,
    preco double precision,
    ativo boolean,
    cor character varying,
    ordem integer,
    criado_em timestamp without time zone,
    tem_variacao_caracteristica boolean DEFAULT false,
    caracteristicas jsonb DEFAULT '[]'::jsonb,
    recorrencia_sugerida_dias integer DEFAULT 0
);


ALTER TABLE public.servicos OWNER TO "user";

--
-- Name: transbordo; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.transbordo (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    telefone character varying NOT NULL,
    status character varying,
    criado_em timestamp without time zone
);


ALTER TABLE public.transbordo OWNER TO "user";

--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.usuarios (
    id uuid NOT NULL,
    empresa_id uuid NOT NULL,
    email character varying NOT NULL,
    senha_hash character varying NOT NULL,
    criado_em timestamp without time zone,
    role character varying DEFAULT 'client'::character varying
);


ALTER TABLE public.usuarios OWNER TO "user";

--
-- Name: agendamentos id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.agendamentos ALTER COLUMN id SET DEFAULT nextval('public.agendamentos_id_seq'::regclass);


--
-- Name: estado_auxiliar id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.estado_auxiliar ALTER COLUMN id SET DEFAULT nextval('public.estado_auxiliar_id_seq'::regclass);


--
-- Name: itens_agendamento id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_agendamento ALTER COLUMN id SET DEFAULT nextval('public.itens_agendamento_id_seq'::regclass);


--
-- Name: lista_espera id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.lista_espera ALTER COLUMN id SET DEFAULT nextval('public.lista_espera_id_seq'::regclass);


--
-- Name: series_recorrencia id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.series_recorrencia ALTER COLUMN id SET DEFAULT nextval('public.series_recorrencia_id_seq'::regclass);


--
-- Data for Name: agendamentos; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.agendamentos (id, empresa_id, lead_id, servico_id, servico_nome, servico_duracao, data, hora_inicio, hora_fim, status, observacao, motivo_cancelamento, lembrete_cliente_enviado, lembrete_profissional_enviado, criado_em, atualizado_em, endereco) FROM stdin;
\.


--
-- Data for Name: bloqueios; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.bloqueios (id, empresa_id, data, hora_inicio, hora_fim, motivo) FROM stdin;
\.


--
-- Data for Name: campanhas; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.campanhas (id, empresa_id, codigo_ref, nome, origem, criado_em, descricao) FROM stdin;
\.


--
-- Data for Name: campos_customizados; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.campos_customizados (id, empresa_id, chave, label, tipo, obrigatorio, opcoes, ordem, ativo, criado_em, dependencias) FROM stdin;
97ae4826-683e-45b0-9332-dfbb118404c1	9c8ab728-aaaa-4454-90b8-4d06afd827db	preferencia_treino	Preferência de Treino	opcao_unica	t	["musculacao", "crossfit", "funcional"]	10	t	2026-05-21 04:37:51.516468	\N
435dd77b-20c3-43c0-a062-c4250f55c45f	5b19782c-9b8c-493e-a652-db5491b7a0cd	tipo_seguro	Tipo de Seguro	texto	t	\N	10	t	2026-05-21 05:16:45.014837	\N
ce9dd934-60f2-46b9-969c-804fe0d0f41d	4a376a15-7276-4bb6-b5ad-5329479dcd39	tipo_seguro	Tipo de Seguro	opcao_unica	t	["Plano de Saúde", "Automóvel/Motos", "Outros seguros"]	10	t	2026-05-21 22:13:26.587668	null
2108f48f-1d23-4a9f-ac8e-dbd887ad455f	4a376a15-7276-4bb6-b5ad-5329479dcd39	para_quem	Para quem é o plano?	texto	t	\N	20	t	2026-05-21 22:13:26.589527	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
962971cb-90eb-4ec0-a706-271050d82765	4a376a15-7276-4bb6-b5ad-5329479dcd39	idade_beneficiarios	Idade das pessoas beneficiárias	texto	t	\N	30	t	2026-05-21 22:13:26.589529	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
70a6fb27-ab46-4fa0-8af3-43077ec3cb6e	4a376a15-7276-4bb6-b5ad-5329479dcd39	tem_cnpj_mei	Possui CNPJ ou MEI?	opcao_unica	t	["Sim (CNPJ)", "Sim (MEI)", "Não"]	40	t	2026-05-21 22:13:26.590849	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
766f372f-5985-41a9-bdd3-45cd602858e2	4a376a15-7276-4bb6-b5ad-5329479dcd39	mei_mais_6_meses	Se for MEI, possui mais de 6 meses de abertura?	opcao_unica	f	["Sim", "Não"]	50	t	2026-05-21 22:13:26.590851	{"valores": ["Sim (MEI)"], "campo_pai": "tem_cnpj_mei"}
109317c3-b0af-40ac-82ac-6277f075b25e	4a376a15-7276-4bb6-b5ad-5329479dcd39	cidade_regiao_atendimento	Região/Cidade para atendimento hospitalar	texto	t	\N	60	t	2026-05-21 22:13:26.591771	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
34bd576a-63ed-4881-9528-96d46fbed250	4a376a15-7276-4bb6-b5ad-5329479dcd39	hospital_preferencia	Tem algum hospital de preferência? Se sim, qual?	texto	f	\N	70	t	2026-05-21 22:13:26.591773	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
c1b25c48-4110-4dba-a72b-b6e792c85d0f	4a376a15-7276-4bb6-b5ad-5329479dcd39	plano_atual	Atualmente tem plano de saúde? Se sim, qual e há quanto tempo?	texto	f	\N	80	t	2026-05-21 22:13:26.591774	{"valores": ["Plano de Saúde"], "campo_pai": "tipo_seguro"}
768ba99f-817f-4ffd-bc60-4c4d6b9a8fe4	4a376a15-7276-4bb6-b5ad-5329479dcd39	placa_veiculo	Placa do veículo / moto	texto	t	\N	90	t	2026-05-21 22:13:26.591774	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
18c74e3d-39d7-4914-ad27-365d10e33b5b	4a376a15-7276-4bb6-b5ad-5329479dcd39	cep_pernoite	CEP onde o veículo pernoita	texto	t	\N	100	t	2026-05-21 22:13:26.591775	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
4814b8fa-6ef9-46f9-b6f1-d2ab085269f4	4a376a15-7276-4bb6-b5ad-5329479dcd39	data_nascimento_condutor	Data de nascimento do condutor principal	texto	t	\N	110	t	2026-05-21 22:13:26.591776	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
86704c8d-8b4e-43e7-8945-dc21ae52215d	4a376a15-7276-4bb6-b5ad-5329479dcd39	estado_civil_condutor	Estado civil do condutor principal	opcao_unica	t	["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]	120	t	2026-05-21 22:13:26.592946	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
0059a2cf-d089-4e18-a0ce-caa48836767c	4a376a15-7276-4bb6-b5ad-5329479dcd39	uso_veiculo	Uso é lazer exclusivo ou locomoção diária (trabalho/estudos)?	opcao_unica	t	["Lazer exclusivo", "Locomoção diária (trabalho/estudos)"]	130	t	2026-05-21 22:13:26.592948	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
39c312f7-b797-4f82-8f71-3a0ed97a7f07	4a376a15-7276-4bb6-b5ad-5329479dcd39	garagem_trabalho_escola	No local de trabalho/estudos, possui garagem fechada?	opcao_unica	f	["Sim", "Não"]	140	t	2026-05-21 22:13:26.592949	{"valores": ["Locomoção diária (trabalho/estudos)"], "campo_pai": "uso_veiculo"}
3185106d-e8f3-4ea2-bf2b-77948e5a6a6b	4a376a15-7276-4bb6-b5ad-5329479dcd39	uso_comercial	Uso comercial (visitas a clientes ou fornecedores)?	opcao_unica	t	["Sim", "Não"]	150	t	2026-05-21 22:13:26.592949	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
04375912-fa04-44c9-8447-ba1012785479	4a376a15-7276-4bb6-b5ad-5329479dcd39	uso_aplicativo_entrega	Uso para aplicativo (Uber, 99) ou entrega de mercadorias?	opcao_unica	t	["Sim", "Não"]	160	t	2026-05-21 22:13:26.59295	{"valores": ["Automóvel/Motos"], "campo_pai": "tipo_seguro"}
609c7a8c-b630-445d-a483-fa33b8eb1873	4a376a15-7276-4bb6-b5ad-5329479dcd39	outro_seguro_tipo	Qual tipo de seguro você precisa?	texto	t	\N	170	t	2026-05-21 22:13:26.594286	{"valores": ["Outros seguros"], "campo_pai": "tipo_seguro"}
\.


--
-- Data for Name: cardapio; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.cardapio (id, empresa_id, categoria, nome, descricao, preco, disponivel, ordem, criado_em, atualizado_em) FROM stdin;
3c0f9ac5-87e2-4e09-8ad9-fa458eb61345	a25504f8-e8fe-4990-ba94-37837d4d413f	Lanches	X-Burguer	Pão brioche, hambúrguer de blend artesanal 150g, queijo cheddar derretido e maionese da casa.	18	t	10	2026-05-22 01:51:35.643454	2026-05-22 01:51:35.643458
81f622b6-098b-4578-9ab9-a760d23a6e99	a25504f8-e8fe-4990-ba94-37837d4d413f	Lanches	X-Salada	Pão brioche, hambúrguer 150g, queijo prato, alface crespa, tomate fresco e maionese verde.	20	t	20	2026-05-22 01:51:35.643458	2026-05-22 01:51:35.643459
a988df0c-28c9-430e-b55b-bf2224811f22	a25504f8-e8fe-4990-ba94-37837d4d413f	Lanches	X-Tudo	Pão, hambúrguer 150g, queijo, presunto, bacon crocante, ovo, alface, tomate e batata palha.	28	t	30	2026-05-22 01:51:35.64346	2026-05-22 01:51:35.64346
26ce4f0a-82a7-4be9-b5fb-7b561b9c5df9	a25504f8-e8fe-4990-ba94-37837d4d413f	Lanches	X-Bacon	Pão brioche, hambúrguer 150g, muito bacon crocante, cheddar e barbecue artesanal.	24	t	40	2026-05-22 01:51:35.643461	2026-05-22 01:51:35.643461
9ede8c62-d3da-4dff-99ba-586a3b50e0dd	a25504f8-e8fe-4990-ba94-37837d4d413f	Acompanhamentos	Batata Frita Média	Batata palito crocante e sequinha com sal e páprica leve.	12	t	50	2026-05-22 01:51:35.643462	2026-05-22 01:51:35.643462
23ab4400-9777-4813-a269-351500ff1f17	a25504f8-e8fe-4990-ba94-37837d4d413f	Acompanhamentos	Batata Frita com Bacon e Cheddar	Porção generosa de fritas cobertas com molho cheddar cremoso e farofa de bacon.	22	t	60	2026-05-22 01:51:35.643463	2026-05-22 01:51:35.643463
567f3302-c076-4d79-a7f4-f64a63138263	a25504f8-e8fe-4990-ba94-37837d4d413f	Acompanhamentos	Anéis de Cebola	Anéis de cebola empanados super crocantes (10 unidades).	14	t	70	2026-05-22 01:51:35.64347	2026-05-22 01:51:35.64347
8ce81531-69d7-4d5d-8ebe-047a036becf9	a25504f8-e8fe-4990-ba94-37837d4d413f	Bebidas	Coca-Cola Lata	Refrigerante lata 350ml trincando de gelada.	6	t	80	2026-05-22 01:51:35.643471	2026-05-22 01:51:35.643471
c28015d5-398d-447c-9ee2-fe0d49b1da01	a25504f8-e8fe-4990-ba94-37837d4d413f	Bebidas	Guaraná Antarctica Lata	Refrigerante lata 350ml gelada.	6	t	90	2026-05-22 01:51:35.643472	2026-05-22 01:51:35.643472
ebbf49f3-ac7b-4f3b-99d6-1a8ef47880a2	a25504f8-e8fe-4990-ba94-37837d4d413f	Bebidas	Suco de Laranja 500ml	Suco de laranja natural e espremido na hora.	9.5	t	100	2026-05-22 01:51:35.643473	2026-05-22 01:51:35.643473
6f9f8294-1736-476c-b49c-7290e2ef1d20	a25504f8-e8fe-4990-ba94-37837d4d413f	Bebidas	Água Sem Gás	Garrafa de água mineral 500ml.	4	t	110	2026-05-22 01:51:35.643473	2026-05-22 01:51:35.643474
\.


--
-- Data for Name: codigos_recuperacao; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.codigos_recuperacao (id, usuario_id, codigo, expira_em, criado_em) FROM stdin;
\.


--
-- Data for Name: comunicado_logs; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.comunicado_logs (id, comunicado_id, telefone, status, erro, criado_em) FROM stdin;
\.


--
-- Data for Name: comunicados; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.comunicados (id, empresa_id, mensagem, data_programada, status, total_membros, enviados, erros, criado_em, enviado_em, imagem_url) FROM stdin;
\.


--
-- Data for Name: configuracoes; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.configuracoes (id, empresa_id, config, atualizado_em) FROM stdin;
fc286919-816b-4bd8-b61d-664d187acdec	9c8ab728-aaaa-4454-90b8-4d06afd827db	{"missao": "Motivar e guiar alunos na jornada fitness, oferecendo suporte rápido e agendamento de aulas.", "planos": {"vip": 149, "basico": 89}, "tom_voz": "Energético, motivador e muito amigável.", "endereco": "Av. Eng. Antônio Francisco de Paula Souza, 123 - Campinas", "horarios": {"sabado": "08h às 14h", "semana": "06h às 22h"}, "pagamentos": ["Cartão", "Pix", "Dinheiro"], "nome_agente": "Rosana", "professores": [{"nome": "Ricardo Silva", "especialidade": "Musculação e Hipertrofia"}, {"nome": "Ana Beatriz", "especialidade": "Yoga e Pilates"}], "cargo_agente": "Personal Trainer Virtual", "nome_empresa": "Prime Fit"}	2026-05-25 05:45:45.12437
757f7260-80e9-4e01-8ef3-288a1658d355	638ba618-40b8-42e0-b1c4-45f0d2360975	{"missao": "Ajudar clientes a encontrarem o imóvel ideal com segurança e transparência.", "regras": ["Sempre pergunte qual o objetivo do cliente (comprar ou alugar).", "Pergunte a faixa de preço que o cliente está buscando.", "Convide para uma visita ao showroom."], "tom_voz": "Profissional, sério e muito atencioso aos detalhes.", "horarios": "Segunda a Sexta das 09:00 às 18:00", "servicos": ["Venda", "Locação", "Avaliação de Imóveis"], "nome_agente": "Roberto", "cargo_agente": "Consultor Imobiliário", "documentacao": "Trabalhamos com toda a assessoria para financiamento bancário.", "nome_empresa": "Viver Bem Imóveis", "oportunidades": [{"tipo": "Apartamento", "valor": "R$ 750.000", "bairro": "Cambuí"}, {"tipo": "Casa", "valor": "R$ 1.200.000", "bairro": "Taquaral"}]}	2026-05-20 17:17:15.005843
43277e32-d9c9-44bf-a715-3451530a935f	4a376a15-7276-4bb6-b5ad-5329479dcd39	{"faq": [], "aulas": [], "missao": "Proteger o que é mais importante para nossos clientes com transparência e agilidade.", "tom_voz": "Consultivo e Seguro", "endereco": "", "horarios": {"sabado": "", "semana": "", "domingo": ""}, "objetivo": "Coletar dados para cotação de seguros e solicitar documentos.", "timezone": "America/Sao_Paulo", "nome_agente": "Alice", "professores": [], "conhecimento": [{"conteudo": "requisitos: saber se é pessoa fisica ou juridica. Valor: 50 reais pra CPF e 100 para CNPJ.", "categoria": "seguro de moto"}], "nome_empresa": "Piccolo Seguros", "prompt_sistema": "Você é um corretor de seguros digital de alta performance. Seu tom é consultivo, profissional e que passa segurança. Seu objetivo é entender as necessidades do cliente, qualificar o lead (coletando dados para cotação) e solicitar o envio de documentos (CNH, CRLV, carteirinha atual) para preparar a melhor proposta de plano de saúde, odonto ou seguro auto/moto.", "planos_detalhados": [], "aviso_vencimento_1": 7, "aviso_vencimento_2": 3, "aviso_vencimento_3": 0, "telefones_ignorados": [], "regras_comportamento": []}	2026-05-20 19:51:53.208032
a637418a-6c5c-4670-974c-997ec3835307	5b19782c-9b8c-493e-a652-db5491b7a0cd	{"reengagement_pending_prompt": "Lembre o lead de que precisamos das informações pendentes ({campos_pendentes}) para prosseguir.", "reengagement_pending_enabled": true, "reengagement_inactivity_prompt": "Olá! Gostaria de saber se ficou com alguma dúvida sobre nossos seguros.", "reengagement_inactivity_enabled": true, "reengagement_pending_delay_hours": 1, "reengagement_inactivity_delay_hours": 2}	2026-05-21 05:16:45.016424
65660ce5-c72e-4ff9-ac7b-a2d36c580946	a25504f8-e8fe-4990-ba94-37837d4d413f	{"identidade": {"cargo": "Atendente Virtual", "missao": "Auxiliar clientes a fazerem seus pedidos de lanches.", "tom_voz": "Simpático e ágil."}, "nome_agente": "Rosana", "nome_empresa": "Piccolo Lanches Teste", "taxa_entrega": 5.0, "whatsapp_cozinha": "5519999993333", "telefones_ignorados": ["5519999991111", "5519999992222"]}	2026-05-23 07:35:19.410735
17c364ed-36f2-472e-9371-dbd59b757ee5	35b0463e-e816-404a-af24-d5ff6d729fd5	{"agenda": {"aprovacao_manual": false, "lembrete_cliente_min": 60, "aprovacao_timeout_min": 60, "whatsapp_profissional": "5511977770000", "lembrete_profissional_hora": "08:00"}, "missao": "Proporcionar autoestima e bem-estar através de cuidados personalizados de beleza e estética.", "tom_voz": "Caloroso, sofisticado e acolhedor.", "endereco": "Av. Paulista, 1000 - Bela Vista - São Paulo", "horarios": {"sabado": "09h às 18h", "semana": "09h às 20h"}, "nome_agente": "Juliana", "cargo_agente": "Especialista em Beleza Virtual", "nome_empresa": "Studio Elegance"}	2026-05-25 05:46:56.322199
\.


--
-- Data for Name: disponibilidade; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.disponibilidade (id, empresa_id, dia_semana, data_especifica, hora_inicio, hora_fim, intervalo_min, ativo) FROM stdin;
\.


--
-- Data for Name: documentos_legais; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.documentos_legais (id, empresa_id, titulo, categoria, conteudo, fonte, ativo, criado_em) FROM stdin;
\.


--
-- Data for Name: documentos_seguro; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.documentos_seguro (id, lead_id, empresa_id, tipo, arquivo_nome, arquivo_path, arquivo_url, mimetype, ocr_processado, ocr_resultado, ocr_confianca, recebido_em) FROM stdin;
\.


--
-- Data for Name: empresas; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.empresas (id, nome, telefone_whatsapp, telefone_proprietario, webhook_token, ativo, criado_em, etapas_funil, slug, valor_mensalidade, data_expiracao_teste, cupom_vendedor, data_criacao, evolution_instance, plano, limite_conversas_mes, conversas_mes_atual, data_reset_contador, tokens_input_mes, tokens_output_mes, nicho) FROM stdin;
a25504f8-e8fe-4990-ba94-37837d4d413f	Piccolo Lanches Teste	5511999999999	5519999994444	3b6f2734-c0c1-4112-b67f-f12e1e62d38f	t	2026-05-22 01:51:35.619389	["novo", "curioso", "interessado", "agendado"]	piccolo-lanches-teste	0	\N	\N	2026-05-22 01:51:35.616131	piccolo_lanches_instance	trial	100	0	\N	0	0	lanchonete
9c8ab728-aaaa-4454-90b8-4d06afd827db	Prime Fit	5511999990000	55119996737713	primefit-token-123	t	2026-05-08 23:37:05.25137	["novo", "curioso", "interessado", "agendado"]	prime-fit	0	\N	\N	2026-05-10 19:34:24.999542	inst-primefit-9c8a	trial	100	0	\N	0	0	academia
4a376a15-7276-4bb6-b5ad-5329479dcd39	Piccolo Corretora Teste	551999996363	551944444444	token_teste_corretora	t	2026-05-20 19:00:28.475434	["novo_lead", "em_atendimento", "documentos_pendentes", "em_cotacao"]	piccolo-corretora-teste	97	\N	\N	2026-05-20 19:00:28.470465	instance_teste	ilimitado	100	0	\N	0	0	corretora
638ba618-40b8-42e0-b1c4-45f0d2360975	Viver Bem Imóveis	5511988880000	\N	viverbem-token-456	t	2026-05-09 23:30:44.149738	["novo", "curioso", "interessado", "agendado"]	viver-bem-imoveis	0	\N	\N	2026-05-10 19:34:24.999542	\N	trial	100	0	\N	0	0	imobiliaria
35b0463e-e816-404a-af24-d5ff6d729fd5	Studio Elegance	5511977770000	\N	studioelegance-token-789	t	2026-05-25 05:45:45.143277	["novo", "curioso", "interessado", "agendado"]	studio-elegance	0	\N	\N	2026-05-25 05:45:45.140243	\N	trial	100	0	\N	0	0	beleza
5b19782c-9b8c-493e-a652-db5491b7a0cd	Seguros Teste Reengajamento	55119692482	55118692482	85af0402-7599-46eb-80c3-7ddda1ae3924	t	2026-05-21 05:16:45.011776	["novo", "curioso", "interessado", "agendado"]	seguros-teste-reeng-692482	0	\N	\N	2026-05-21 05:16:45.008946	instancia_teste_reeng	trial	100	0	\N	625	81	corretora
\.


--
-- Data for Name: empresas_clientes; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.empresas_clientes (id, empresa_id, nome_empresa, cnpj, regime_tributario, contato_nome, contato_telefone, ativo, criado_em) FROM stdin;
\.


--
-- Data for Name: estado_auxiliar; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.estado_auxiliar (id, empresa_id, estado_json, atualizado_em) FROM stdin;
\.


--
-- Data for Name: eventos; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.eventos (id, empresa_id, lead_id, tipo, metadata, "timestamp") FROM stdin;
6ed7deed-6a51-49d6-8838-d99b91bc8fb5	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	perguntou_preco	{}	2026-05-08 23:37:05.284645
d429013f-312e-4bf1-a16b-5eed1f36c28c	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	intencao_duvida	{}	2026-05-09 23:47:50.339842
48c0d3e6-99dd-49b0-a15d-8f51d9ee0a91	9c8ab728-aaaa-4454-90b8-4d06afd827db	fb445d42-c135-4285-9f38-8d35863c7ac3	intencao_plano	{}	2026-05-09 23:48:06.558914
75c81a4c-5467-4c39-a217-1a288fc0e70e	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	intencao_duvida	{}	2026-05-09 23:51:51.328395
d79bae06-547d-4a79-821c-04a7369b5e1c	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	intencao_duvida	{}	2026-05-09 23:58:04.714641
0f349394-2f2c-424b-9736-e98097508e5b	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	intencao_duvida	{}	2026-05-09 23:59:55.349967
6b098767-01e0-4a5d-9f83-01e8de254710	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	perguntou_preco	{}	2026-05-10 19:38:53.677474
445a582e-d6a1-44aa-b342-5ff74d0f6d91	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	iniciou_conversa	{}	2026-05-20 19:05:44.252364
8d374ce6-754c-44f1-b8ff-31e018b9c23c	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	fez_pergunta	{}	2026-05-20 19:05:45.660019
7cc427f1-70b2-4385-a7de-039caf65cda0	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	fez_pergunta	{}	2026-05-20 19:05:48.258089
8c1d40ad-d411-4214-8446-1f2c797505a4	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	fez_pergunta	{}	2026-05-20 19:05:51.047393
1ee45834-7f58-4b55-a386-bda70f9b331d	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	perguntou_saudacao	{}	2026-05-21 02:27:08.130697
a21ce5f9-9375-4437-b74b-34f0baa35241	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	perguntou_plano	{}	2026-05-21 02:27:10.199038
86ed409f-a013-455f-a418-5aca10224c79	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	perguntou_saudacao	{}	2026-05-21 02:27:12.629957
294e45d2-e6d0-4bd2-b933-f1b7df1dcac2	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	fez_pergunta	{}	2026-05-21 02:27:15.487978
66b2c105-d359-4ad1-949b-9d67255a41a8	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	fez_pergunta	{}	2026-05-21 02:27:17.797006
228fad9d-28fa-4d39-9cc1-61cb21d126c3	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	fez_pergunta	{}	2026-05-21 02:27:20.565974
ef573098-4f49-440a-ab95-ab7dc6052230	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	fez_pergunta	{}	2026-05-21 02:27:23.291142
5b388eda-e8f4-490b-b983-8435f6281b50	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	transbordo_confirmado	{}	2026-05-21 02:27:25.651396
7dbfa6d5-3578-4b36-b20e-86102d5cb2c1	9c8ab728-aaaa-4454-90b8-4d06afd827db	3eb328ec-9cd9-4ea8-931d-989e6f719dcb	campanha_atribuida	{"origem": "facebook", "codigo_ref": "FB-TESTE-123", "campanha_id": "e5bb0f21-ff65-4040-85ff-d22a838bba53"}	2026-05-21 03:05:01.087203
\.


--
-- Data for Name: followups_seguro; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.followups_seguro (id, lead_id, empresa_id, tipo, mensagem, enviado_em, resultado) FROM stdin;
\.


--
-- Data for Name: itens_agendamento; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.itens_agendamento (id, agendamento_id, servico_id, servico_nome, duracao_min, preco) FROM stdin;
\.


--
-- Data for Name: itens_pedido; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.itens_pedido (id, pedido_id, cardapio_id, nome, preco_unit, quantidade, observacao) FROM stdin;
25160657-af0b-4299-abaf-c896a17a3d0b	9b4e527c-00f5-490f-b07f-0f6c947f1231	a988df0c-28c9-430e-b55b-bf2224811f22	X-Tudo	28	2	\N
f39241cd-27ff-46d8-8b6e-bdc059c407f1	9b4e527c-00f5-490f-b07f-0f6c947f1231	9ede8c62-d3da-4dff-99ba-586a3b50e0dd	Batata Frita Média	12	1	\N
0ca6dd26-b046-47b8-be71-80e5e74d9696	9b4e527c-00f5-490f-b07f-0f6c947f1231	8ce81531-69d7-4d5d-8ebe-047a036becf9	Coca-Cola Lata	6	1	\N
\.


--
-- Data for Name: leads; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.leads (id, empresa_id, telefone, nome, stage, visit_offer_made, criado_em, atualizado_em, utm_source, utm_campaign, canal_entrada, dados_customizados) FROM stdin;
4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	9c8ab728-aaaa-4454-90b8-4d06afd827db	5511999999999	\N	curioso	f	2026-05-08 23:37:05.271135	2026-05-08 23:37:05.271138	\N	\N	organico	{}
0143d2de-b34d-4fd2-8309-7c286c7209dc	638ba618-40b8-42e0-b1c4-45f0d2360975	5511912345678	\N	novo	f	2026-05-09 23:47:50.321889	2026-05-09 23:47:50.321894	\N	\N	organico	{}
fb445d42-c135-4285-9f38-8d35863c7ac3	9c8ab728-aaaa-4454-90b8-4d06afd827db	5511912345678	\N	curioso	f	2026-05-09 23:48:06.537769	2026-05-09 23:48:06.554272	\N	\N	organico	{}
b38dfff0-8c6a-402f-92e5-82548dedb8b5	a25504f8-e8fe-4990-ba94-37837d4d413f	5511999990000	\N	novo	f	2026-05-22 01:55:42.240137	2026-05-22 01:55:55.571595	\N	\N	organico	{"pedido_mesa": null, "pedido_modo": null, "pedido_itens": [], "pedido_estado": "pedido_feito", "pedido_endereco": null, "pedido_nome_balcao": null}
14d2667a-01c6-4353-a8f4-ec85979d3b6b	4a376a15-7276-4bb6-b5ad-5329479dcd39	5519996737713	\N	novo	f	2026-05-21 02:27:06.050875	2026-05-28 19:21:46.098965	\N	\N	organico	{"agenda_obs": "", "agenda_data": null, "agenda_hora": null, "agenda_estado": "inicio", "agenda_servico_id": null, "agenda_servico_nome": null}
0a04e5a1-9e33-4672-b3bc-5f9b6cc12d4b	5b19782c-9b8c-493e-a652-db5491b7a0cd	5511999998888	Carlos Silveira	triagem	f	2026-05-21 05:16:45.027384	2026-05-21 13:13:32.722543	\N	\N	organico	{"reengajamento_fluxo_ativo": "pending", "reengajamento_passo_atual": 1, "ultimo_reengajamento_pendente": "2026-05-21T02:16:45.028957", "reengajamento_ultimo_timestamp": "2026-05-21T13:13:29.442145"}
fe5c1c31-18e7-4a64-91e5-48f6576aeb87	4a376a15-7276-4bb6-b5ad-5329479dcd39	5519987654321	Thiago Silva	primeiro_contato	f	2026-05-20 19:05:44.244233	2026-05-20 19:05:44.259201	\N	\N	organico	{}
3eb328ec-9cd9-4ea8-931d-989e6f719dcb	9c8ab728-aaaa-4454-90b8-4d06afd827db	559999999991	\N	novo	f	2026-05-21 03:05:01.069345	2026-05-21 03:05:01.080622	facebook	FB-TESTE-123	facebook	{}
003c963e-82b2-43eb-a31b-67f71bc3c6ed	9c8ab728-aaaa-4454-90b8-4d06afd827db	559999999992	\N	novo	f	2026-05-21 03:05:01.095872	2026-05-21 03:05:01.101477	\N	INSTA-PROMO-XYZ	ads_generico	{}
d617f524-ccfd-4656-9b1e-0419634eb7c7	9c8ab728-aaaa-4454-90b8-4d06afd827db	559999999993	\N	novo	f	2026-05-21 03:05:16.555468	2026-05-21 03:05:16.555472	\N	\N	organico	{}
6a0e3cea-8784-4f4d-8ba2-76ee228db082	9c8ab728-aaaa-4454-90b8-4d06afd827db	5511962561623	Carlos Teste Dinamico	triagem	f	2026-05-21 04:33:05.416557	2026-05-21 04:33:05.427065	\N	\N	organico	{"preferencia_treino": "crossfit"}
6c64eaa5-92a7-4faf-bb43-99c925985a03	9c8ab728-aaaa-4454-90b8-4d06afd827db	5511980814770	Carlos Teste Dinamico	triagem	f	2026-05-21 04:37:51.508649	2026-05-21 04:37:51.519572	\N	\N	organico	{"preferencia_treino": "crossfit"}
\.


--
-- Data for Name: leads_seguro; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.leads_seguro (id, empresa_id, telefone, nome_contato, nome_segurado, relacao_segurado, tipo_seguro, produto_especifico, idade_segurado, tem_cnpj, e_mei, tem_plano_anterior, plano_anterior_nome, mais_de_6_meses, regiao, hospitais_preferidos, marca_modelo, ano_fabricacao, ano_modelo, placa, cep_pernoite, uso_veiculo, tem_garagem, condutor_principal, idade_condutor, bonus_classe, tipo_imovel, cep_imovel, metragem, imovel_proprio, docs_recebidos, docs_pendentes, stage, canal_entrada, template_raw, resumo_ia, observacoes, seguradora_escolhida, valor_proposta, data_proposta_enviada, data_vencimento_apolice, numero_apolice, ultimo_followup_em, followup_count, motivo_perda, criado_em, atualizado_em) FROM stdin;
fe5c1c31-18e7-4a64-91e5-48f6576aeb87	4a376a15-7276-4bb6-b5ad-5329479dcd39	5519987654321	Thiago Silva	Thiago Silva	proprio	saude	\N	32	f	t	t	Amil 400	\N	Campinas/SP	Vera Cruz, Samaritano	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	["cnh_ou_rg"]	primeiro_contato	template	\n    Novo contato solicitando cotação de seguro!\n    Nome: Thiago Silva\n    Contato: +5519987654321\n    Tipo: Plano de Saúde\n    Pra quem: Próprio\n    Idade: 32\n    Tem CNPJ: Não\n    É MEI: Não\n    Plano Anterior: Sim\n    Nome do Plano Anterior: Amil 400\n    Região: Campinas/SP\n    Hospitais Preferidos: Vera Cruz, Samaritano\n    	\N	\N	\N	\N	\N	\N	\N	\N	0	\N	2026-05-20 19:05:44.27367	2026-05-20 19:05:50.331101
14d2667a-01c6-4353-a8f4-ec85979d3b6b	4a376a15-7276-4bb6-b5ad-5329479dcd39	5519996737713	\N	Eduardo Targine Capella	\N	saude	\N	41	\N	\N	f	\N	\N	Campinas	Unimed	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	[]	novo	organico	\N	\N	\N	\N	\N	\N	\N	\N	\N	0	\N	2026-05-21 02:27:06.05922	2026-05-21 02:27:25.654381
\.


--
-- Data for Name: lista_espera; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.lista_espera (id, empresa_id, lead_id, servico_id, data, data_flexivel, posicao, status, notificado_em, criado_em) FROM stdin;
\.


--
-- Data for Name: membros_academia; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.membros_academia (id, empresa_id, nome, telefone, data_vencimento, plano_nome, ativo, aviso_7_dias_enviado, aviso_3_dias_enviado, aviso_vencido_enviado, importado_em, atualizado_em) FROM stdin;
\.


--
-- Data for Name: mensagens; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.mensagens (id, empresa_id, lead_id, tipo, mensagem, intencao, "timestamp") FROM stdin;
0fbd7e53-4454-4619-be9d-11c7cbfa9bf0	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	usuario	Olá, gostaria de saber os preços	preco	2026-05-08 23:37:05.278253
36fc41fc-0ffa-4c98-9091-9b14c917ed0a	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	agente	Olá! Nossos planos começam em R$ 80,00 mensais no básico.	\N	2026-05-08 23:37:05.278272
1c4743b7-1fbc-4a26-9c27-bade5353e4e7	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	usuario	Olá, o que você tem disponível no Cambuí?	duvida	2026-05-09 23:47:50.331096
2ca06201-30e3-4380-9cb6-26ac9100c141	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	agente	Olá! No Cambuí, temos disponível um apartamento com o valor de R$ 750.000. \n\nGostaria de saber se você está interessado em comprar ou alugar, e qual a faixa de preço que está buscando. Além disso, ficaria feliz em convidá-lo para uma visita ao showroom para conhecermos melhor suas necessidades.	\N	2026-05-09 23:47:53.82353
d5d3e38d-f9fb-4ff1-a59f-cb96733a2eb7	9c8ab728-aaaa-4454-90b8-4d06afd827db	fb445d42-c135-4285-9f38-8d35863c7ac3	usuario	Quais são os planos de vocês?	plano	2026-05-09 23:48:06.548717
72a85789-01cd-4056-801e-b6d5a6005c4e	9c8ab728-aaaa-4454-90b8-4d06afd827db	fb445d42-c135-4285-9f38-8d35863c7ac3	agente	Nós oferecemos dois planos:\n\n1. **Plano VIP:** R$ 150\n2. **Plano Básico:** R$ 99\n\nAmbos os planos oferecem acesso às nossas instalações e horários. Se precisar de mais informações ou ajuda para escolher um plano, estou aqui para ajudar! 😊	\N	2026-05-09 23:48:08.459371
ce16b969-7e74-4c35-a496-4c8658bca088	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	usuario	Olá, o que você tem disponível no Cambuí?	duvida	2026-05-09 23:51:51.31593
49e157b4-e630-4ffa-8225-7afbd469478d	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	agente	Olá! No Cambuí, temos disponível um apartamento com o valor de R$ 750.000. \n\nGostaria de saber se você está interessado em comprar ou alugar, e qual a faixa de preço que está buscando. Também posso convidá-lo para uma visita ao showroom para discutirmos suas necessidades mais a fundo.	\N	2026-05-09 23:51:52.92611
54a8390d-4ca2-434f-8144-b75842dfbf70	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	usuario	Olá, o que você tem no Cambuí?	duvida	2026-05-09 23:58:04.699023
01946aa7-9d09-4b50-ac01-efaf89abcca1	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	agente	Olá! No Cambuí, temos um apartamento disponível por R$ 750.000. \n\nGostaria de saber se você está buscando comprar ou alugar, e qual a faixa de preço que você tem em mente. Sinta-se à vontade para me dizer, e posso convidá-lo para uma visita ao showroom para conversarmos mais sobre suas necessidades!	\N	2026-05-09 23:58:07.05691
5e05b7ca-7c92-48cc-b7c6-e4f216c1bed4	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	usuario	Olá	duvida	2026-05-09 23:59:55.333997
0af832c8-4212-4c4e-89d8-7cdca8f58415	638ba618-40b8-42e0-b1c4-45f0d2360975	0143d2de-b34d-4fd2-8309-7c286c7209dc	agente	Olá! Como posso ajudá-lo hoje? Se você está interessado em imóveis, estou aqui para ajudar a encontrar o que você precisa.	\N	2026-05-09 23:59:58.124216
6df5f394-b405-4033-a67c-d80428d4996e	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	usuario	Olá! Qual o valor da mensalidade e que horas vocês abrem?	preco	2026-05-10 19:38:53.670465
764f85b3-8597-4091-8344-9e6fffb5da5b	9c8ab728-aaaa-4454-90b8-4d06afd827db	4a87c8ae-4dc5-485d-bc02-0e948bd9e1fd	agente	Olá! Temos dois planos disponíveis:\n\n1. **Plano Básico**: R$ 80/mês (acesso à musculação).\n2. **Plano VIP**: R$ 150/mês (musculação + aulas de Zumba, Yoga, Crossfit).\n\nQuanto aos horários, abrimos de segunda a sexta das 06h às 22h e aos sábados das 08h às 14h. \n\nAh, só para lembrar, estamos fechados no momento. Se precisar de mais informações ou quiser discutir qual plano é melhor para você, estou aqui para ajudar! 💪✨	\N	2026-05-10 19:38:58.104582
7deb6d02-91c6-485f-b718-b8641e481cef	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	usuario	[Template Piccolo]: \n    Novo contato solicitando cotação de seguro!\n    Nome: Thiago Silva\n    Contato: +5519987654321\n    Tipo: Plano de Saúde\n    Pra quem: Próprio\n    Idade: 32\n    Tem CNPJ: Não\n    É MEI: Não\n    Plano Anterior: Sim\n    Nome do Plano Anterior: Amil 400\n    Região: Campinas/SP\n    Hospitais Preferidos: Vera Cruz, Samaritano\n    	preco	2026-05-20 19:05:44.280202
937e18cd-3f15-4396-a68a-4227da08d8fe	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	agente	Olá, *Thiago*! 👋\n\nSou o(a) *Rosana*, assistente virtual da *Piccolo Seguros*.\n\nRecebi sua solicitação de cotação para *Plano de Saúde* e já estou com suas informações aqui. 😊\n\nEm breve nossa equipe vai entrar em contato com as melhores opções para você.\n\nEnquanto isso, posso te ajudar com qualquer dúvida sobre coberturas, carências ou funcionamento do plano. É só perguntar!	\N	2026-05-20 19:05:45.060918
254b465b-5ee7-411e-8f65-54b038e1ccbd	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	usuario	Olá, gostaria de saber se vocês têm convênio com o hospital Vera Cruz?	duvida	2026-05-20 19:05:45.075265
98468a0d-6d0a-4060-bee7-058dd7bf313f	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	agente	Oi, *Thiago*! \n\nSim, temos convênio com o hospital *Vera Cruz*. Ele é uma das opções que podemos incluir na sua cotação de plano de saúde. \n\nSe precisar de mais informações ou tiver outras dúvidas, estou à disposição! 😊	\N	2026-05-20 19:05:47.63529
8e9ebd4d-2469-4459-ac5a-ba8165583380	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	usuario	Sim, eu tenho MEI também, esqueci de falar. Pode atualizar?	duvida	2026-05-20 19:05:47.661532
b8173083-81ca-4f3a-b696-0d3e88170738	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	agente	Claro, *Thiago*! Vou atualizar suas informações agora. \n\nVocê mencionou que tem *MEI*. \n\nSe precisar de mais alguma coisa, é só avisar! 😊	\N	2026-05-20 19:05:50.334956
48e324e8-9027-4da0-af48-36e3ef541fad	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	usuario	Perfeito! Meu CPF é 123.456.789-00.	duvida	2026-05-20 19:05:50.350991
a7201e6e-7500-47ca-9d1a-85d738484639	4a376a15-7276-4bb6-b5ad-5329479dcd39	fe5c1c31-18e7-4a64-91e5-48f6576aeb87	agente	Obrigado por compartilhar, *Thiago*! \n\nVou registrar seu CPF como *123.456.789-00*. \n\nSe tiver mais alguma informação ou dúvida, estou aqui para ajudar! 😊	\N	2026-05-20 19:05:56.645436
0d48461e-182b-4829-9b13-4ee766d41f69	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	eae, qual o seu nome?	saudacao	2026-05-21 02:27:08.118212
15d63f98-faae-493d-8b32-dc0b84e7ce65	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Olá! Eu sou a Alice, sua assistente virtual da Piccolo Seguros. Como posso te ajudar hoje? \n\n[ATUALIZAR_LEAD: nome_segurado=Cliente]	\N	2026-05-21 02:27:09.320286
51036b2f-847c-460a-afdd-a947cdc19566	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	preciso de cotacao para plano de saúde	plano	2026-05-21 02:27:10.188819
b6884da1-fb08-4b30-a854-dfad4ffc28df	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Claro! Para começarmos a cotação do plano de saúde, você pode me informar sua data de nascimento ou idade? \n\n[ATUALIZAR_LEAD: tipo_seguro=saude]	\N	2026-05-21 02:27:11.415318
6e77e864-eed6-4ad9-a54e-2a2173ffc9bd	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	Eduardo Targine Capella	saudacao	2026-05-21 02:27:12.61862
d8a98b86-016b-4bb4-bbaf-888b4b235071	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Ótimo, Eduardo! Agora que tenho seu nome, você pode me informar sua data de nascimento ou idade? \n\n[ATUALIZAR_LEAD: nome_segurado=Eduardo Targine Capella]	\N	2026-05-21 02:27:14.617507
c01f272f-1c2c-4279-92cf-9fd0684247e5	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	41 anos	duvida	2026-05-21 02:27:15.472628
9e624816-4355-4399-b169-a52d9ae69013	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Perfeito, Eduardo! Agora que tenho sua idade, você possui algum plano de saúde anterior? \n\n[ATUALIZAR_LEAD: idade_segurado=41]	\N	2026-05-21 02:27:16.887849
b48dd9a3-5e53-4a86-82e2-eccd7af02ea5	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	nenhum dos dois	duvida	2026-05-21 02:27:17.785595
6758ea34-9d9f-455a-a638-e46312b0560e	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Entendi, Eduardo! Então você não possui plano anterior. Agora, você pode me informar se tem alguma preferência de hospitais ou região para o plano de saúde? \n\n[ATUALIZAR_LEAD: tem_plano_anterior=false]	\N	2026-05-21 02:27:19.392763
76c06acd-d2db-43a8-ac21-7a47833822d8	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	sim, Unimed	duvida	2026-05-21 02:27:20.555217
95d3beb8-b700-4f37-83e6-edec210afc78	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Ótimo, Eduardo! Agora que sei que você tem preferência pela Unimed, só mais uma pergunta: você possui CNPJ ou MEI? \n\n[ATUALIZAR_LEAD: hospitais_preferidos=Unimed]	\N	2026-05-21 02:27:22.033356
dc398b77-c652-464f-9d07-abcaa5f65d38	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	região de Campinas	duvida	2026-05-21 02:27:23.280189
891eb8d7-d833-4619-823a-86fde3ae5eb5	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	agente	Perfeito, Eduardo! Agora que temos sua preferência pela Unimed e a região de Campinas, vou repassar todas as informações coletadas para a Corretora Responsável. Eles entrarão em contato em instantes com as melhores opções para você. Obrigado pela sua paciência!\n\n[SOLICITAR_HUMANO: motivo=Triagem concluída - pronto para cotação]  \n[ATUALIZAR_LEAD: regiao=Campinas]	\N	2026-05-21 02:27:26.495382
2bda36cb-d0b2-47f5-857d-cf75a09a2918	5b19782c-9b8c-493e-a652-db5491b7a0cd	0a04e5a1-9e33-4672-b3bc-5f9b6cc12d4b	agente	Olá, qual seguro você deseja cotar?	\N	2026-05-21 02:16:45.028957
098e3b23-91d5-4f96-ace8-e6fffde2abde	5b19782c-9b8c-493e-a652-db5491b7a0cd	0a04e5a1-9e33-4672-b3bc-5f9b6cc12d4b	agente	Olá! Notamos que faltou preencher o Tipo de Seguro para prosseguir com sua cotação. Vamos finalizar?	\N	2026-05-21 05:16:45.118899
bbf21228-f537-4d21-83ad-9c934c040735	5b19782c-9b8c-493e-a652-db5491b7a0cd	0a04e5a1-9e33-4672-b3bc-5f9b6cc12d4b	agente	Oi, Carlos! 😊 Só passando para lembrar que precisamos saber qual Tipo de Seguro você está interessado para seguir com a sua cotação. Pode me contar?	\N	2026-05-21 13:13:32.000626
8ceeba8f-a0e6-459a-b34a-701e5ade38c2	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	usuario	Olá, boa noite!	\N	2026-05-22 01:55:42.245174
3b9e2eeb-9951-4f9b-99f0-c4fc5a1fa9c5	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	agente	Olá, boa noite! Como posso te ajudar hoje? Está pensando em fazer um pedido? 😊	\N	2026-05-22 01:55:43.891567
50aa9b5a-8097-4bc5-9a65-60d18e58dfe8	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	usuario	Quero por Delivery na Rua dos Pinheiros, 123	\N	2026-05-22 01:55:43.898817
fc741d9d-ca7f-438c-9291-120f49c8badf	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	agente	Perfeito! Vou registrar seu pedido para delivery na Rua dos Pinheiros, 123. \n\nAgora, você gostaria de escolher algum lanche, acompanhamento ou bebida do nosso cardápio? 😊	\N	2026-05-22 01:55:46.382195
4a0a1c4e-4b6d-4243-a2b0-d02576b4fe62	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	usuario	Quero dois X-Tudo, uma Batata Frita Média e uma Coca-Cola	\N	2026-05-22 01:55:46.391164
f3bed4bf-0015-4532-b68b-dccd25033bd5	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	agente	Ótima escolha! Vou adicionar ao seu pedido:\n\n- 2 X-Tudo\n- 1 Batata Frita Média\n- 1 Coca-Cola Lata\n\nVou registrar esses itens agora. Um momento, por favor! 😊	\N	2026-05-22 01:55:49.749818
95425e58-bf6f-4058-a19d-024b1c138493	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	usuario	Pode fechar a conta e confirmar pra mim	\N	2026-05-22 01:55:49.759105
dd4acfab-7570-4efd-8914-8084437d4e58	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	agente	Claro! Aqui está o resumo do seu pedido:\n\n- 2x X-Tudo (R$ 28.00 cada)\n- 1x Batata Frita Média (R$ 12.00)\n- 1x Coca-Cola Lata (R$ 6.00)\n\n**Subtotal:** R$ 74.00  \n**Taxa de entrega:** R$ 5.00  \n**Total Geral:** R$ 79.00\n\nVocê confirma esse pedido? 😊	\N	2026-05-22 01:55:52.245051
167be43e-cf57-4abd-bf36-df42f00758af	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	usuario	Sim, está tudo perfeito! Confirmo o pedido.	\N	2026-05-22 01:55:52.253614
e699d2bc-97c0-423f-a9c6-7b3c99b21ac3	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	agente	Perfeito! Seu pedido foi confirmado. Aqui está o resumo novamente:\n\n- 2x X-Tudo (R$ 28.00 cada)\n- 1x Batata Frita Média (R$ 12.00)\n- 1x Coca-Cola Lata (R$ 6.00)\n\n**Subtotal:** R$ 74.00  \n**Taxa de entrega:** R$ 5.00  \n**Total Geral:** R$ 79.00\n\nAgradecemos pela sua escolha! Seu pedido será entregue em breve na Rua dos Pinheiros, 123. 😊\n\n👉 *O número do seu pedido é: #1*.	\N	2026-05-22 01:55:55.583754
48a8ae8f-bc4d-4ee1-b104-be54b5a09155	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	Oi	\N	2026-05-28 19:13:32.009362
7f2f6e58-87f1-425b-b7cc-028e2da8506e	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	Oi	\N	2026-05-28 19:14:13.516133
e7daf7f6-71d9-4d20-8d76-05d862ebd11a	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	Oi	\N	2026-05-28 19:14:49.062856
70de1b25-203e-4fd1-9347-6605aff759e5	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	usuario	Oi	\N	2026-05-28 19:21:43.322142
a65948f1-0a05-4c70-ae9f-f1b9964111ea	4a376a15-7276-4bb6-b5ad-5329479dcd39	14d2667a-01c6-4353-a8f4-ec85979d3b6b	assistente	Olá! Como posso ajudá-lo hoje? Se você estiver interessado em agendar um serviço ou tiver alguma dúvida, estou aqui para ajudar! \n\n[INICIO]	\N	2026-05-28 19:21:46.110518
\.


--
-- Data for Name: obrigacoes_fiscais; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.obrigacoes_fiscais (id, empresa_id, empresa_cliente_id, titulo, descricao, prazo, status, aviso_enviado, criado_em) FROM stdin;
\.


--
-- Data for Name: pedidos; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pedidos (id, empresa_id, lead_id, numero_pedido, modo, status, total, observacao, endereco, nome_balcao, numero_mesa, criado_em, atualizado_em) FROM stdin;
9b4e527c-00f5-490f-b07f-0f6c947f1231	a25504f8-e8fe-4990-ba94-37837d4d413f	b38dfff0-8c6a-402f-92e5-82548dedb8b5	1	delivery	entregue	79	\N	Rua dos Pinheiros, 123	\N	\N	2026-05-22 01:55:54.567925	2026-05-22 01:55:57.872999
\.


--
-- Data for Name: prompt_templates; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.prompt_templates (id, nome_nicho, prompt_sistema, tom_voz, missao, objetivo, etapas_funil, criado_em, nicho) FROM stdin;
90bd4452-1148-4b79-8bf7-ccdb597f0a11	Clínica	Você é uma assistente virtual de uma clínica médica. Seu tom é profissional, empático e cuidadoso. Seu objetivo é agendar consultas e triar necessidades básicas.	Profissional e Empático	Proporcionar saúde e bem-estar com excelência.	Marcar consultas médicas.	["novo", "curioso", "triagem", "agendado"]	2026-05-10 19:50:41.884001	generico
80afe94c-b884-4ced-9107-0343cacbf698	Imobiliária	Você é uma assistente virtual de uma imobiliária de luxo. Seu tom é elegante, prestativo e focado em detalhes. Seu objetivo é qualificar leads e agendar visitas a imóveis.	Elegante e Sofisticado	Encontrar o lar dos sonhos para nossos clientes.	Agendar visitas a imóveis.	["novo", "curioso", "qualificado", "visita_marcada"]	2026-05-10 19:50:41.884008	generico
2cb697e6-250c-44cc-a6ed-8c47846055d8	Corretora de Seguros	Você é um corretor de seguros digital de alta performance. Seu tom é consultivo, profissional e que passa segurança. Seu objetivo é entender as necessidades do cliente, qualificar o lead (coletando dados para cotação) e solicitar o envio de documentos (CNH, CRLV, carteirinha atual) para preparar a melhor proposta de plano de saúde, odonto ou seguro auto/moto.	Consultivo e Seguro	Proteger o que é mais importante para nossos clientes com transparência e agilidade.	Coletar dados para cotação de seguros e solicitar documentos.	["novo_lead", "em_atendimento", "documentos_pendentes", "em_cotacao"]	2026-05-20 19:44:45.834053	corretora
c1c4e1d3-e803-4e16-8691-d48437037249	lanchonete	Você é a Rosana, atendente virtual simpática e ágil da Lanchonete Piccolo.\nSua missão é ajudar os clientes a montarem e confirmarem seus pedidos de lanches no WhatsApp de forma acolhedora, eficiente e organizada.\n\n=== DIRETRIZES DE FLUXO E ESTADOS ===\nO fluxo de atendimento da lanchonete segue etapas rígidas controladas pelo estado atual da conversa. O estado atual é passado no contexto como 'estado_pedido' ('inicio', 'montando', 'confirmando', 'pedido_feito').\nVocê deve agir estritamente conforme o estado atual:\n\n1. ESTADO: 'inicio'\n   - Cumprimente o cliente de forma amigável com um sorriso virtual (emojis).\n   - Pergunte como ele gostaria de fazer o pedido: 🛵 Delivery (Entrega), 🛍️ Retirada no Balcão ou 🍽️ Consumo na Mesa.\n   - Não passe para a escolha de pratos até que o cliente informe o modo de atendimento!\n   - Se ele escolher 'Mesa', pergunte qual o número da mesa.\n   - Se escolher 'Delivery', solicite o endereço completo de entrega.\n   - IMPORTANTE: Assim que o modo for definido, insira a tag técnica [DEFINIR_MODO: modo=valor] (onde valor é 'delivery', 'balcao' ou 'mesa') e, se aplicável, [ATUALIZAR_LEAD: endereco=...] ou [ATUALIZAR_LEAD: mesa=...]. Isso mudará o estado do pedido para 'montando'.\n\n2. ESTADO: 'montando'\n   - Apresente as categorias do nosso Cardápio de forma organizada e limpa.\n   - Anote os itens e as quantidades escolhidas pelo cliente.\n   - Confirme sabores, bebidas e acompanhamentos (ex: pontos de carne, se quer gelo e limão).\n   - Sempre informe a disponibilidade dos itens antes de adicioná-los.\n   - Sempre que o cliente pedir ou adicionar um item, inclua a tag técnica no final da resposta: [ADICIONAR_ITEM: nome=..., quantidade=..., obs=...].\n   - Quando o cliente disser que terminou de escolher tudo e quiser fechar a conta/pedido, você deve levá-lo para a confirmação.\n   - Escreva o resumo provisório e adicione a tag técnica [SOLICITAR_CONFIRMACAO] para mudar o estado para 'confirmando'.\n\n3. ESTADO: 'confirmando'\n   - Exiba um resumo detalhado e legível do pedido contendo:\n     * Itens selecionados com preços individuais e quantidade\n     * Modo de atendimento escolhido\n     * Endereço (se delivery) ou número da mesa (se mesa)\n     * Taxa de entrega (se delivery, cobrar R$ 5,00 fixo)\n     * Valor Total Geral do pedido\n   - Pergunte claramente: 'Podemos confirmar o seu pedido?'\n   - Se o cliente confirmar, você DEVE anexar a tag técnica na última linha: [CONFIRMAR_PEDIDO]. Isso criará o pedido no banco e mudará o estado para 'pedido_feito'.\n   - Se ele quiser alterar algo, remova itens usando [REMOVER_ITEM: nome=...] e volte o estado para 'montando'.\n\n4. ESTADO: 'pedido_feito'\n   - Diga que o pedido foi enviado com sucesso para a nossa cozinha! 🎉\n   - Informe o número do pedido gerado (ex: Pedido #42).\n   - Explique que ele receberá avisos automáticos aqui no WhatsApp sobre o preparo e despacho.\n   - Fique à disposição para qualquer outra dúvida ou ajuste rápido.\n\n=== REGRAS DE OURO ===\n- Colete apenas um dado de cada vez (sem bombardear o cliente com formulários).\n- NUNCA ofereça produtos que não estejam listados explicitamente no Cardápio abaixo.\n- Seja ágil, use emojis adequados e mantenha uma formatação impecável.	Acolhedora, ágil e extremamente simpática com emojis.	Anotar e organizar pedidos de lanches dos clientes integrando-os diretamente com a cozinha.	Concluir a montagem do pedido e obter a confirmação explícita do cliente.	["novo", "interessado", "fechado"]	2026-05-22 01:51:35.609228	lanchonete
4ee1f940-9c69-4249-a9ae-27479ac6cabc	Beleza e Estética	Você é uma assistente virtual de um salão de beleza e estética. Seu tom é caloroso, amigável e focado em bem-estar. Seu objetivo é ajudar clientes a escolherem serviços, sugerir recorrências e conduzi-los ao agendamento de forma suave e personalizada.	Caloroso, Elegante e Acolhedor	Realçar a beleza única de cada pessoa com carinho e profissionalismo.	Agendar procedimentos de beleza, gerenciar lista de espera e sugerir recorrências.	["novo", "curioso", "agendado"]	2026-05-25 05:45:44.224491	beleza
7c66a309-1ed0-4edd-ad99-6feb6527c38d	Academia	Você é uma assistente virtual de atendimento ao público de uma academia. Seu tom é prestativo, amigável e focado em bem-estar. Seu objetivo é acolher os alunos e interessados, tirar dúvidas sobre planos, horários de funcionamento, regras, modalidades e fornecer suporte de forma rápida e eficiente.	Prestativo, Acolhedor e Educado	Facilitar o acesso à informação e apoiar a jornada de bem-estar dos alunos.	Atendimento ao público e suporte geral para tirar dúvidas de alunos e interessados.	["novo", "em_atendimento", "resolvido"]	2026-05-10 19:50:41.883993	academia
\.


--
-- Data for Name: series_recorrencia; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.series_recorrencia (id, empresa_id, lead_id, servico_id, intervalo_dias, ultimo_agendamento, proximo_sugerido, ativo, criado_em) FROM stdin;
\.


--
-- Data for Name: servicos; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.servicos (id, empresa_id, nome, descricao, duracao_min, preco, ativo, cor, ordem, criado_em, tem_variacao_caracteristica, caracteristicas, recorrencia_sugerida_dias) FROM stdin;
777913a5-aaa9-43a4-98ad-9c0647cec507	9c8ab728-aaaa-4454-90b8-4d06afd827db	Higienizacao Sofá	limpeza geral	120	180	t	#10b981	0	2026-05-24 15:28:03.962709	f	[]	0
9c1f7b5d-1fe4-4932-a209-db39a6f0fd1b	35b0463e-e816-404a-af24-d5ff6d729fd5	Corte Feminino	Corte de cabelo feminino personalizado.	60	120	t	#8b5cf6	1	2026-05-25 05:46:56.331371	t	{"curto": {"preco": 100.0, "duracao": 45}, "longo": {"preco": 150.0, "duracao": 75}}	30
65d153e5-8b92-4a61-9f2a-4ab511dfb5e6	35b0463e-e816-404a-af24-d5ff6d729fd5	Escova	Lavagem e escova modeladora.	30	60	t	#ec4899	2	2026-05-25 05:46:56.331381	t	{"curto": {"preco": 50.0, "duracao": 30}, "longo": {"preco": 80.0, "duracao": 45}}	7
c8a80bf7-20fe-4825-8361-69bbb4a85626	35b0463e-e816-404a-af24-d5ff6d729fd5	Manicure	Cuidado das unhas das mãos com cutilagem e esmaltação.	45	45	t	#10b981	3	2026-05-25 05:46:56.331386	f	null	14
f75130dd-71b1-443a-9e3a-2907d09be95a	35b0463e-e816-404a-af24-d5ff6d729fd5	Designer de Sobrancelhas	Design personalizado de sobrancelhas.	30	50	t	#3b82f6	4	2026-05-25 05:46:56.331392	f	null	21
\.


--
-- Data for Name: transbordo; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.transbordo (id, empresa_id, telefone, status, criado_em) FROM stdin;
fd0ec52e-2689-4a71-a524-c5b01b6f069b	4a376a15-7276-4bb6-b5ad-5329479dcd39	5519996737713	pausado	2026-05-21 02:27:25.656659
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.usuarios (id, empresa_id, email, senha_hash, criado_em, role) FROM stdin;
9f685e9b-e54e-43cf-9350-46a96ae4124d	9c8ab728-aaaa-4454-90b8-4d06afd827db	academia@teste.com	$2b$12$njVf27T7Z7.0AGNkjqiSU.R4LPnDWSpKf.YucWUsom4gBkkKdxp6G	2026-05-10 00:08:05.710861	client
c21f4b5e-6497-46ae-a47a-f82295506948	638ba618-40b8-42e0-b1c4-45f0d2360975	imoveis@teste.com	$2b$12$03/GqdZFE0fnvD7nW/Z/k.baSQcsbm0mq4wjvplxKyNea2YoJTKvK	2026-05-10 00:08:06.013788	client
871bc728-84ed-4002-b295-b1c536b372b0	4a376a15-7276-4bb6-b5ad-5329479dcd39	ale@gmail.com	$2b$12$sZi55Z9gMsmzcFKYvZTha.XafaiZHohT8VJ6nxg/vrkREmEt2K2Eu	2026-05-20 19:45:40.629237	client
362a200d-1050-4d51-9641-c41e53272649	9c8ab728-aaaa-4454-90b8-4d06afd827db	admin@primefit.com.br	$2b$12$PvzEp9qaHR34NRuVwnfzuuMoRtS5vVcb/tBAjh0f30a8lYPY.FdnC	2026-05-08 23:40:50.39693	client
ac07fbd1-5574-42d2-b4ea-f778cae75acc	35b0463e-e816-404a-af24-d5ff6d729fd5	beleza@teste.com	$2b$12$H7NZ9VibqScRYhxYB74nmOqH9Sn8o/f3yk6svAhCOYoNKIV6gYzBW	2026-05-25 05:46:56.333512	client
\.


--
-- Name: agendamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.agendamentos_id_seq', 1, false);


--
-- Name: estado_auxiliar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.estado_auxiliar_id_seq', 1, false);


--
-- Name: itens_agendamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.itens_agendamento_id_seq', 1, false);


--
-- Name: lista_espera_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.lista_espera_id_seq', 1, false);


--
-- Name: series_recorrencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.series_recorrencia_id_seq', 1, false);


--
-- Name: agendamentos agendamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_pkey PRIMARY KEY (id);


--
-- Name: bloqueios bloqueios_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.bloqueios
    ADD CONSTRAINT bloqueios_pkey PRIMARY KEY (id);


--
-- Name: campanhas campanhas_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.campanhas
    ADD CONSTRAINT campanhas_pkey PRIMARY KEY (id);


--
-- Name: campos_customizados campos_customizados_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.campos_customizados
    ADD CONSTRAINT campos_customizados_pkey PRIMARY KEY (id);


--
-- Name: cardapio cardapio_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.cardapio
    ADD CONSTRAINT cardapio_pkey PRIMARY KEY (id);


--
-- Name: codigos_recuperacao codigos_recuperacao_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.codigos_recuperacao
    ADD CONSTRAINT codigos_recuperacao_pkey PRIMARY KEY (id);


--
-- Name: comunicado_logs comunicado_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.comunicado_logs
    ADD CONSTRAINT comunicado_logs_pkey PRIMARY KEY (id);


--
-- Name: comunicados comunicados_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.comunicados
    ADD CONSTRAINT comunicados_pkey PRIMARY KEY (id);


--
-- Name: configuracoes configuracoes_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.configuracoes
    ADD CONSTRAINT configuracoes_pkey PRIMARY KEY (id);


--
-- Name: disponibilidade disponibilidade_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.disponibilidade
    ADD CONSTRAINT disponibilidade_pkey PRIMARY KEY (id);


--
-- Name: documentos_legais documentos_legais_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.documentos_legais
    ADD CONSTRAINT documentos_legais_pkey PRIMARY KEY (id);


--
-- Name: documentos_seguro documentos_seguro_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.documentos_seguro
    ADD CONSTRAINT documentos_seguro_pkey PRIMARY KEY (id);


--
-- Name: empresas_clientes empresas_clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas_clientes
    ADD CONSTRAINT empresas_clientes_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_evolution_instance_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_evolution_instance_key UNIQUE (evolution_instance);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_slug_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_slug_key UNIQUE (slug);


--
-- Name: empresas empresas_telefone_whatsapp_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_telefone_whatsapp_key UNIQUE (telefone_whatsapp);


--
-- Name: empresas empresas_webhook_token_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_webhook_token_key UNIQUE (webhook_token);


--
-- Name: estado_auxiliar estado_auxiliar_empresa_id_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.estado_auxiliar
    ADD CONSTRAINT estado_auxiliar_empresa_id_key UNIQUE (empresa_id);


--
-- Name: estado_auxiliar estado_auxiliar_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.estado_auxiliar
    ADD CONSTRAINT estado_auxiliar_pkey PRIMARY KEY (id);


--
-- Name: eventos eventos_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.eventos
    ADD CONSTRAINT eventos_pkey PRIMARY KEY (id);


--
-- Name: followups_seguro followups_seguro_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.followups_seguro
    ADD CONSTRAINT followups_seguro_pkey PRIMARY KEY (id);


--
-- Name: itens_agendamento itens_agendamento_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_agendamento
    ADD CONSTRAINT itens_agendamento_pkey PRIMARY KEY (id);


--
-- Name: itens_pedido itens_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_pedido
    ADD CONSTRAINT itens_pedido_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: leads_seguro leads_seguro_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.leads_seguro
    ADD CONSTRAINT leads_seguro_pkey PRIMARY KEY (id);


--
-- Name: lista_espera lista_espera_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.lista_espera
    ADD CONSTRAINT lista_espera_pkey PRIMARY KEY (id);


--
-- Name: membros_academia membros_academia_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.membros_academia
    ADD CONSTRAINT membros_academia_pkey PRIMARY KEY (id);


--
-- Name: mensagens mensagens_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.mensagens
    ADD CONSTRAINT mensagens_pkey PRIMARY KEY (id);


--
-- Name: obrigacoes_fiscais obrigacoes_fiscais_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.obrigacoes_fiscais
    ADD CONSTRAINT obrigacoes_fiscais_pkey PRIMARY KEY (id);


--
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- Name: prompt_templates prompt_templates_nome_nicho_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.prompt_templates
    ADD CONSTRAINT prompt_templates_nome_nicho_key UNIQUE (nome_nicho);


--
-- Name: prompt_templates prompt_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.prompt_templates
    ADD CONSTRAINT prompt_templates_pkey PRIMARY KEY (id);


--
-- Name: series_recorrencia series_recorrencia_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.series_recorrencia
    ADD CONSTRAINT series_recorrencia_pkey PRIMARY KEY (id);


--
-- Name: servicos servicos_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.servicos
    ADD CONSTRAINT servicos_pkey PRIMARY KEY (id);


--
-- Name: transbordo transbordo_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.transbordo
    ADD CONSTRAINT transbordo_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: ix_campanhas_codigo_ref; Type: INDEX; Schema: public; Owner: user
--

CREATE UNIQUE INDEX ix_campanhas_codigo_ref ON public.campanhas USING btree (codigo_ref);


--
-- Name: agendamentos agendamentos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: agendamentos agendamentos_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE SET NULL;


--
-- Name: agendamentos agendamentos_servico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_servico_id_fkey FOREIGN KEY (servico_id) REFERENCES public.servicos(id) ON DELETE SET NULL;


--
-- Name: bloqueios bloqueios_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.bloqueios
    ADD CONSTRAINT bloqueios_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: campanhas campanhas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.campanhas
    ADD CONSTRAINT campanhas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: campos_customizados campos_customizados_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.campos_customizados
    ADD CONSTRAINT campos_customizados_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: cardapio cardapio_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.cardapio
    ADD CONSTRAINT cardapio_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: codigos_recuperacao codigos_recuperacao_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.codigos_recuperacao
    ADD CONSTRAINT codigos_recuperacao_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: comunicado_logs comunicado_logs_comunicado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.comunicado_logs
    ADD CONSTRAINT comunicado_logs_comunicado_id_fkey FOREIGN KEY (comunicado_id) REFERENCES public.comunicados(id);


--
-- Name: comunicados comunicados_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.comunicados
    ADD CONSTRAINT comunicados_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: configuracoes configuracoes_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.configuracoes
    ADD CONSTRAINT configuracoes_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: disponibilidade disponibilidade_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.disponibilidade
    ADD CONSTRAINT disponibilidade_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: documentos_legais documentos_legais_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.documentos_legais
    ADD CONSTRAINT documentos_legais_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: documentos_seguro documentos_seguro_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.documentos_seguro
    ADD CONSTRAINT documentos_seguro_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: documentos_seguro documentos_seguro_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.documentos_seguro
    ADD CONSTRAINT documentos_seguro_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads_seguro(id) ON DELETE CASCADE;


--
-- Name: empresas_clientes empresas_clientes_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.empresas_clientes
    ADD CONSTRAINT empresas_clientes_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: estado_auxiliar estado_auxiliar_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.estado_auxiliar
    ADD CONSTRAINT estado_auxiliar_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: eventos eventos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.eventos
    ADD CONSTRAINT eventos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: eventos eventos_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.eventos
    ADD CONSTRAINT eventos_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: followups_seguro followups_seguro_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.followups_seguro
    ADD CONSTRAINT followups_seguro_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: followups_seguro followups_seguro_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.followups_seguro
    ADD CONSTRAINT followups_seguro_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads_seguro(id) ON DELETE CASCADE;


--
-- Name: itens_agendamento itens_agendamento_agendamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_agendamento
    ADD CONSTRAINT itens_agendamento_agendamento_id_fkey FOREIGN KEY (agendamento_id) REFERENCES public.agendamentos(id) ON DELETE CASCADE;


--
-- Name: itens_agendamento itens_agendamento_servico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_agendamento
    ADD CONSTRAINT itens_agendamento_servico_id_fkey FOREIGN KEY (servico_id) REFERENCES public.servicos(id) ON DELETE SET NULL;


--
-- Name: itens_pedido itens_pedido_cardapio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_pedido
    ADD CONSTRAINT itens_pedido_cardapio_id_fkey FOREIGN KEY (cardapio_id) REFERENCES public.cardapio(id) ON DELETE SET NULL;


--
-- Name: itens_pedido itens_pedido_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.itens_pedido
    ADD CONSTRAINT itens_pedido_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- Name: leads leads_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: leads_seguro leads_seguro_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.leads_seguro
    ADD CONSTRAINT leads_seguro_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: leads_seguro leads_seguro_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.leads_seguro
    ADD CONSTRAINT leads_seguro_id_fkey FOREIGN KEY (id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: lista_espera lista_espera_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.lista_espera
    ADD CONSTRAINT lista_espera_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: lista_espera lista_espera_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.lista_espera
    ADD CONSTRAINT lista_espera_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: lista_espera lista_espera_servico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.lista_espera
    ADD CONSTRAINT lista_espera_servico_id_fkey FOREIGN KEY (servico_id) REFERENCES public.servicos(id) ON DELETE CASCADE;


--
-- Name: membros_academia membros_academia_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.membros_academia
    ADD CONSTRAINT membros_academia_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: mensagens mensagens_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.mensagens
    ADD CONSTRAINT mensagens_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: mensagens mensagens_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.mensagens
    ADD CONSTRAINT mensagens_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: obrigacoes_fiscais obrigacoes_fiscais_empresa_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.obrigacoes_fiscais
    ADD CONSTRAINT obrigacoes_fiscais_empresa_cliente_id_fkey FOREIGN KEY (empresa_cliente_id) REFERENCES public.empresas_clientes(id);


--
-- Name: obrigacoes_fiscais obrigacoes_fiscais_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.obrigacoes_fiscais
    ADD CONSTRAINT obrigacoes_fiscais_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: pedidos pedidos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: pedidos pedidos_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE SET NULL;


--
-- Name: series_recorrencia series_recorrencia_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.series_recorrencia
    ADD CONSTRAINT series_recorrencia_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: series_recorrencia series_recorrencia_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.series_recorrencia
    ADD CONSTRAINT series_recorrencia_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: series_recorrencia series_recorrencia_servico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.series_recorrencia
    ADD CONSTRAINT series_recorrencia_servico_id_fkey FOREIGN KEY (servico_id) REFERENCES public.servicos(id) ON DELETE CASCADE;


--
-- Name: servicos servicos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.servicos
    ADD CONSTRAINT servicos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: transbordo transbordo_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.transbordo
    ADD CONSTRAINT transbordo_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: usuarios usuarios_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict MxGUnC4S7u1c4gdhBfnroWiiUBEk5TqLvgE5PGaZe8LMd37NV5PQBgIKrjl1usU

