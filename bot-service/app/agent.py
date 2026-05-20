from app.openai_client import perguntar

def montar_prompt(config: dict, intencao: str, stage: str, contexto_tempo: str, sentimento: str = "neutro") -> str:
    # 1. Identidade do Agente (Dinâmica - Prioriza campos planos do Dashboard)
    identidade = config.get('identidade', {})
    nome_agente = config.get('nome_agente') or identidade.get('nome') or 'Rosana'
    cargo = config.get('cargo_agente') or identidade.get('cargo') or 'Assistente Virtual'
    nome_empresa = config.get('nome_empresa') or identidade.get('empresa') or 'Empresa'
    missao = config.get('missao') or identidade.get('missao') or 'Auxiliar clientes com clareza e eficiência.'
    tom_voz = config.get('tom_voz') or identidade.get('tom_voz') or 'Amigável e profissional.'
    instrucoes_adicionais = config.get('prompt_sistema') or config.get('instrucoes') or ''
    nicho = config.get('nicho', 'generico')
    documentos = config.get('documentos', [])

    # 1.1 Substituição automática de placeholders para evitar nomes genéricos do template
    def limpar_placeholders(texto):
        if not texto: return ""
        texto = texto.replace("[NOME_DA_ACADEMIA]", nome_empresa)
        texto = texto.replace("[NOME_DA_EMPRESA]", nome_empresa)
        texto = texto.replace("[NOME_DO_AGENTE]", nome_agente)
        return texto

    missao = limpar_placeholders(missao)
    tom_voz = limpar_placeholders(tom_voz)
    instrucoes_adicionais = limpar_placeholders(instrucoes_adicionais)
    
    # DEBUG: Log para verificar o que está sendo lido do banco
    print(f"DEBUG PROMPT -> Nome: {nome_agente} | Empresa: {nome_empresa} | Cargo: {cargo}")
    
    # 2. Base de Conhecimento (Dinâmica)
    secoes_conhecimento = ""
    conhecimento_raw = config.get('conhecimento', [])
    
    # Processa o conhecimento independente se for lista ou dicionário
    if isinstance(conhecimento_raw, list):
        # Formato moderno do Dashboard: [{"categoria": "...", "conteudo": "..."}]
        for item in conhecimento_raw:
            if isinstance(item, dict):
                titulo = item.get('categoria') or item.get('titulo') or 'Informação'
                conteudo = item.get('conteudo') or item.get('resposta') or ''
                if conteudo:
                    secoes_conhecimento += f"\n=== {titulo.upper()} ===\n{conteudo}\n"
            elif isinstance(item, str) and item:
                secoes_conhecimento += f"- {item}\n"
                
    elif isinstance(conhecimento_raw, dict):
        # Formato de dicionário (legado ou específico)
        for titulo, conteudo in conhecimento_raw.items():
            if not conteudo: continue
            secoes_conhecimento += f"\n=== {titulo.replace('_', ' ').upper()} ===\n"
            if isinstance(conteudo, list):
                for subitem in conteudo:
                    secoes_conhecimento += f"- {subitem}\n"
            else:
                secoes_conhecimento += f"{conteudo}\n"

    # 2.0.2 - Planos e Mensalidades (Dinamizados)
    planos_detalhados = config.get('planos_detalhados', [])
    if isinstance(planos_detalhados, list) and planos_detalhados:
        secoes_conhecimento += "\n=== PLANOS E MENSALIDADES ===\n"
        for p in planos_detalhados:
            if isinstance(p, dict):
                nome = p.get('nome', 'Plano')
                valor = p.get('valor', 0)
                ciclo = p.get('periodicidade', 'mensal')
                obs = p.get('descricao', '')
                secoes_conhecimento += f"- {nome}: R$ {valor} ({ciclo})"
                if obs: secoes_conhecimento += f" | Obs: {obs}"
                secoes_conhecimento += "\n"

    # 2.0.3 - Horários de Funcionamento (Dinamizados)
    horarios = config.get('horarios', {})
    if horarios:
        secoes_conhecimento += "\n=== HORÁRIO DE FUNCIONAMENTO ===\n"
        secoes_conhecimento += f"- Segunda a Sexta: {horarios.get('semana', 'Não informado')}\n"
        secoes_conhecimento += f"- Sábados: {horarios.get('sabado', 'Não informado')}\n"
        secoes_conhecimento += f"- Domingos e Feriados: {horarios.get('domingo', 'Fechado')}\n"

    # 2.0.4 - Professores (Dinamizados)
    professores = config.get('professores', [])
    if isinstance(professores, list) and professores:
        secoes_conhecimento += "\n=== PROFESSORES E EQUIPE ===\n"
        for prof in professores:
            if isinstance(prof, dict):
                nome = prof.get('nome', '')
                esp = prof.get('especialidade', '')
                bio = prof.get('descricao', '') or prof.get('bio', '')
                if nome:
                    secoes_conhecimento += f"- Prof. {nome}"
                    if esp: secoes_conhecimento += f" | Especialidade: {esp}"
                    if bio: secoes_conhecimento += f" | Obs: {bio}"
                    secoes_conhecimento += "\n"

    # 2.0.5 - Grade de Aulas e Modalidades (Dinamizados)
    aulas = config.get('aulas', [])
    if isinstance(aulas, list) and aulas:
        secoes_conhecimento += "\n=== GRADE DE AULAS / MODALIDADES ===\n"
        for aula in aulas:
            if isinstance(aula, dict):
                nome = aula.get('nome', '')
                dias_horarios = aula.get('dias_horarios', '') or aula.get('horario', '')
                prof_nome = aula.get('professor', '') or aula.get('instrutor', '')
                obs = aula.get('descricao', '') or aula.get('detalhes', '')
                if nome:
                    secoes_conhecimento += f"- {nome}"
                    if dias_horarios: secoes_conhecimento += f" | Dias/Horários: {dias_horarios}"
                    if prof_nome: secoes_conhecimento += f" | Professor: {prof_nome}"
                    if obs: secoes_conhecimento += f" | Obs: {obs}"
                    secoes_conhecimento += "\n"

    # Fallback para nicho de academia legado (apenas planos se ainda não houver seções)
    if not secoes_conhecimento and 'planos' in config:
        planos = config.get('planos', {})
        secoes_conhecimento += f"=== PLANOS DA ACADEMIA ===\n{planos}\n"

    # 2.0.1 - Prioridade para FAQ e Conhecimento Geral (se existirem como campos planos)
    faq = config.get('faq', [])
    if isinstance(faq, list) and faq:
        secoes_conhecimento += "\n=== PERGUNTAS FREQUENTES (FAQ) ===\n"
        for item in faq:
            if isinstance(item, dict):
                pergunta = item.get('pergunta') or item.get('question')
                resposta = item.get('resposta') or item.get('answer')
                if pergunta and resposta:
                    secoes_conhecimento += f"P: {pergunta}\nR: {resposta}\n\n"

    # 2.1 Documentos Legais (Específico Contabilidade)
    if nicho == 'contabilidade' and documentos:
        secoes_conhecimento += "\n=== BASE LEGAL E DOCUMENTOS ===\n"
        secoes_conhecimento += "Use as informações abaixo para responder dúvidas técnicas:\n"
        for doc in documentos:
            secoes_conhecimento += f"\n- {doc.get('titulo', 'Documento')}:\n{doc.get('conteudo', '')}\n"

    # 3. Regras e Guardrails
    regras = config.get('regras_comportamento') or config.get('regras')
    if not regras or not isinstance(regras, list):
        regras = [
            "Identificar a necessidade do usuário com clareza.",
            "Ser direto, objetivo e empático.",
            "Nunca inventar informações que não estão listadas na base de conhecimento (como preços, horários, planos, professores ou modalidades).",
            "Se o usuário perguntar sobre professores, equipe, modalidades ou grade de aulas e essa informação não estiver descrita explicitamente na base de conhecimento, diga educadamente que não sabe e ofereça encaminhar para o atendimento humano.",
            "Utilizar emojis com moderação para manter um tom amigável.",
            "Se o usuário estiver frustrado ou pedir explicitamente, ofereça atendimento humano."
        ]
    else:
        # Garante que as regras de segurança fundamentais estão sempre presentes
        regras_seguranca = [
            "Nunca inventar informações que não estão listadas na base de conhecimento (como preços, horários, planos, professores ou modalidades).",
            "Se o usuário perguntar sobre professores, equipe, modalidades ou grade de aulas e essa informação não estiver descrita explicitamente na base de conhecimento, diga educadamente que não sabe e ofereça encaminhar para o atendimento humano."
        ]
        for r_seg in regras_seguranca:
            if not any(r_seg[:30] in r for r in regras):
                regras.append(r_seg)
    regras_str = "\n".join([f"{i+1}. {regra}" for i, regra in enumerate(regras)])

    return f"""
Você é {nome_agente}, {cargo} da {nome_empresa}.

=== SUA MISSÃO ===
{missao}

=== SEU TOM DE VOZ ===
{tom_voz}

=== INSTRUÇÕES ADICIONAIS ===
{instrucoes_adicionais}

=== NICHO DE ATUAÇÃO ===
Você atua no nicho: {nicho.upper()}
{"[IMPORTANTE: Você é um assistente de contabilidade. Seja preciso com termos técnicos e use a base legal fornecida.]" if nicho == 'contabilidade' else ""}

=== CONTEXTO ATUAL ===
{contexto_tempo}
INTENÇÃO DETECTADA: {intencao}
ESTÁGIO DO LEAD NO FUNIL: {stage}
SENTIMENTO DO CLIENTE: {sentimento.upper()}
{ "[ALERTA: O usuário parece frustrado ou irritado. Seja extra empático, calmo e prestativo.]" if sentimento == "negativo" else "" }

=== BASE DE CONHECIMENTO ===
{secoes_conhecimento}

=== REGRAS DE ATENDIMENTO ===
{regras_str}

=== FLUXO DE TRANSBORDO (ATENDIMENTO HUMANO) ===
Você deve detectar quando o cliente precisa de um humano (frustração, pedido explícito ou dúvida complexa).
Nesses casos:
1. Responda com empatia.
2. Pergunte se ele deseja falar com um atendente humano.
3. Adicione a tag [SUGERIR_TRANSBORDO] no final.

Se o cliente confirmar: use a tag [CONFIRMAR_TRANSBORDO].
Se o cliente recusar: use a tag [CANCELAR_TRANSBORDO].
"""

CONTEXTO_AGUARDANDO_CONFIRMACAO = """
O cliente acabou de receber uma sugestão de falar com um atendente humano e você está
aguardando a confirmação dele.

Analise a mensagem do cliente:
- Se ele CONFIRMAR que quer falar com humano (sim, quero, pode chamar, por favor, etc.):
  Responda de forma acolhedora dizendo que já vai chamar um atendente, e inclua a tag [CONFIRMAR_TRANSBORDO]
  Exemplo: "Perfeito! Vou chamar um atendente agora mesmo para te ajudar. Um momento 🙂 [CONFIRMAR_TRANSBORDO]"

- Se ele RECUSAR ou mudar de assunto (não, pode continuar, deixa, tudo bem, etc.):
  Responda normalmente e retome o atendimento sem mencionar o transbordo novamente.
  Inclua a tag [CANCELAR_TRANSBORDO]
  Exemplo: "Claro, sem problema! Pode continuar, estou aqui para ajudar 😊 [CANCELAR_TRANSBORDO]"

Importante: sempre inclua uma das duas tags ([CONFIRMAR_TRANSBORDO] ou [CANCELAR_TRANSBORDO])
"""

def processar_mensagem_dinamica(mensagem_usuario: str, config: dict, intencao: str, stage: str, contexto_tempo: str, historico=None, sentimento: str = "neutro"):
    prompt_dinamico = montar_prompt(config, intencao, stage, contexto_tempo, sentimento)
    return perguntar(mensagem_usuario, prompt_dinamico, historico)

def processar_confirmacao_transbordo(mensagem_usuario: str, historico=None):
    """Usado quando o número está em status 'aguardando' - decide se confirma ou cancela."""
    return perguntar(mensagem_usuario, CONTEXTO_AGUARDANDO_CONFIRMACAO, historico)