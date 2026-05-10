from app.openai_client import perguntar

def montar_prompt(config: dict, intencao: str, stage: str, contexto_tempo: str, sentimento: str = "neutro") -> str:
    # 1. Identidade do Agente (Dinâmica - Prioriza campos planos do Dashboard)
    identidade = config.get('identidade', {})
    nome_agente = config.get('nome_agente') or identidade.get('nome') or 'Rosana'
    cargo = config.get('cargo_agente') or identidade.get('cargo') or 'Assistente Virtual'
    nome_empresa = config.get('nome_empresa') or identidade.get('empresa') or 'Empresa'
    missao = config.get('missao') or identidade.get('missao') or 'Auxiliar clientes com clareza e eficiência.'
    tom_voz = config.get('tom_voz') or identidade.get('tom_voz') or 'Amigável e profissional.'
    
    # DEBUG: Log para verificar o que está sendo lido do banco
    print(f"DEBUG PROMPT -> Nome: {nome_agente} | Empresa: {nome_empresa} | Cargo: {cargo}")
    
    # 2. Base de Conhecimento (Dinâmica)
    secoes_conhecimento = ""
    conhecimento = config.get('conhecimento', {})
    
    # Se não houver 'conhecimento' estruturado, tenta converter o formato antigo de academia
    if not conhecimento and ('planos' in config or 'horarios' in config):
        # Fallback para compatibilidade com o nicho de academia legado
        planos = config.get('planos', {})
        horarios = config.get('horarios', {})
        aulas_vip = config.get('aulas_vip', [])
        professores = config.get('professores', [])
        
        secoes_conhecimento += f"=== INFORMAÇÕES DA ACADEMIA ===\n"
        secoes_conhecimento += f"Planos: {planos}\n"
        secoes_conhecimento += f"Horários: {horarios}\n"
        if aulas_vip: secoes_conhecimento += f"Aulas VIP: {', '.join(aulas_vip)}\n"
        if professores:
            secoes_conhecimento += "\nPROFESSORES:\n" + "\n".join([f"- {p.get('nome', 'N/A')}: {p.get('especialidade', 'N/A')}" for p in professores if isinstance(p, dict)])
    else:
        # Novo formato flexível
        for titulo, conteudo in conhecimento.items():
            secoes_conhecimento += f"\n=== {titulo.replace('_', ' ').upper()} ===\n"
            if isinstance(conteudo, list):
                for item in conteudo:
                    if isinstance(item, dict):
                        # Tenta formatar dicionário de forma legível
                        linha = " | ".join([f"{k}: {v}" for k, v in item.items()])
                        secoes_conhecimento += f"- {linha}\n"
                    else:
                        secoes_conhecimento += f"- {item}\n"
            elif isinstance(conteudo, dict):
                for k, v in conteudo.items():
                    secoes_conhecimento += f"- {k}: {v}\n"
            else:
                secoes_conhecimento += f"{conteudo}\n"

    # 3. Regras e Guardrails
    regras = config.get('regras', [
        "Identificar a necessidade do usuário com clareza.",
        "Ser direto, objetivo e empático.",
        "Nunca inventar informações que não estão listadas na base de conhecimento.",
        "Utilizar emojis com moderação para manter um tom amigável.",
        "Se o usuário estiver frustrado ou pedir explicitamente, ofereça atendimento humano."
    ])
    regras_str = "\n".join([f"{i+1}. {regra}" for i, regra in enumerate(regras)])

    return f"""
Você é {nome_agente}, {cargo} da {nome_empresa}.

=== SUA MISSÃO ===
{missao}

=== SEU TOM DE VOZ ===
{tom_voz}

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