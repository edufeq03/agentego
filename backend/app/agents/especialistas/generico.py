from app.agents.base_agent import BaseAgent
from app.openai_client import perguntar

class EspecialistaGenerico(BaseAgent):
    nome = "EspecialistaGenerico"

    def processar(self, mensagem: str, contexto: dict, historico: list) -> tuple[str, int, int]:
        prompt = self._montar_prompt(contexto)
        openai_hist = self.montar_historico_openai(historico)
        
        # Injetar o lembrete de tags de forma extremamente direta no final da mensagem do usuário.
        # Isso quebra o comportamento de imitação do histórico e força a extração do dado do turno atual.
        lembrete = (
            "\n\n[INSTRUÇÃO DO SISTEMA: Se o usuário acima acabou de informar ou confirmar qualquer dado "
            "(como nome, idade, objetivo de treino, frequência, etc.), "
            "ou se você concluiu a triagem, você DEVE incluir a tag correspondente ao final da sua resposta, "
            "no formato '[ATUALIZAR_LEAD: campo=valor]' ou '[SOLICITAR_HUMANO: motivo=...]'. "
            "Gere a tag para o dado que ele acabou de fornecer!]"
        )
        mensagem_com_lembrete = mensagem + lembrete
        temperature = contexto.get("config", {}).get("openai_temperature", 0.2)
        
        return perguntar(mensagem_com_lembrete, prompt, openai_hist, temperature=temperature)

    def _montar_prompt(self, ctx: dict) -> str:
        config = ctx["config"]

        nome_agente = ctx["nome_agente"]
        nome_empresa = ctx["nome_empresa"]
        cargo = config.get('cargo_agente') or config.get('identidade', {}).get('cargo') or 'Assistente Virtual'
        missao = config.get('missao') or config.get('identidade', {}).get('missao') or 'Auxiliar clientes com clareza e eficiência.'
        tom_voz = config.get('tom_voz') or config.get('identidade', {}).get('tom_voz') or 'Amigável e profissional.'
        instrucoes_adicionais = config.get('prompt_sistema') or config.get('instrucoes') or ''
        nicho = ctx["nicho"]
        
        # Dados Dinâmicos da Triagem
        campos_pendentes = ctx["triagem_dinamica"]["campos_pendentes"]
        campos_coletados = ctx["triagem_dinamica"]["campos_coletados"]
        
        # Adicionar informações de campanha e recorrência
        campanha_info = ctx.get("campanha", {})
        campanha_cod = campanha_info.get("codigo") or "Nenhuma"
        campanha_orig = campanha_info.get("origem") or "Orgânico"
        campanha_nome = campanha_info.get("nome") or "Nenhum"
        campanha_desc = campanha_info.get("descricao") or "Nenhuma instrução especial de foco cadastrada."
        recorrente_str = "Sim" if ctx.get("lead_recorrente") else "Não"
        lead_nome = ctx.get("lead_nome") or "Cliente"
        retomar_sem_apresentacao = config.get("_retomar_sem_apresentacao", False)

        # Bloco de instrução de retomada (modo retomar_conhecidos)
        instrucao_retomada = ""
        if retomar_sem_apresentacao:
            instrucao_retomada = """
=== [MODO RETOMAR CONTATO CONHECIDO — INSTRUÇÃO OBRIGATÓRIA] ===
Este contato já conversou com você anteriormente e está retomando o contato.
REGRAS DE OURO para esta interação:
1. NÃO se apresente. Não diga "Sou o/a X, assistente da empresa Y" nem variações.
2. NÃO faça perguntas iniciais de triagem (nome, objetivo, etc.) — ele já é conhecido.
3. SE a mensagem dele for uma saudação vaga ("oi", "olá", "e aí", "tudo bem?", etc.):
   → Responda de forma casual e amigável, e pergunte em que pode ajudar. Ex: "Oi! Que bom te ver por aqui de novo 😊 Em que posso ajudar hoje?"
4. SE a mensagem dele contiver uma demanda ou pergunta clara:
   → Responda DIRETAMENTE ao que ele pediu, sem rodeios de apresentação.
   → Exemplo: se ele perguntar sobre um serviço, responda com as informações do serviço imediatamente.
=== [FIM DA INSTRUÇÃO DE RETOMADA] ===
"""

        def limpar_placeholders(texto):
            if not texto: return ""
            texto = texto.replace("[NOME_DA_ACADEMIA]", nome_empresa)
            texto = texto.replace("[NOME_DA_EMPRESA]", nome_empresa)
            texto = texto.replace("[NOME_DO_AGENTE]", nome_agente)
            return texto

        missao = limpar_placeholders(missao)
        tom_voz = limpar_placeholders(tom_voz)
        instrucoes_adicionais = limpar_placeholders(instrucoes_adicionais)

        secoes_conhecimento = self._montar_conhecimento(config)
        regras_str = self._montar_regras(config)

        return f"""{instrucao_retomada}
Você é {nome_agente}, {cargo} da {nome_empresa}.

=== STATUS DO CLIENTE ===
CLIENTE RECORRENTE: {recorrente_str} (Se "Sim", ele já conversou com você anteriormente nesta conversa)

=== INFORMAÇÕES DE ANÚNCIO (CAMPANHA) ===
Origem do Anúncio (UTM Source): {campanha_orig}
Código da Campanha (UTM Campaign): {campanha_cod}
Nome da Campanha: {campanha_nome}
Descrição/Foco da Campanha: {campanha_desc}

=== PERSONALIDADE E TOM (SAUDAÇÃO INTELIGENTE) ===
* RECONHECIMENTO DE ANÚNCIO (Para cliente novo com Campanha ativa): Se o cliente for novo (CLIENTE RECORRENTE = Não) e houver uma Campanha ativa (diferente de 'Nenhuma'), você DEVE iniciar sua primeira resposta contextualizando o anúncio que ele viu com base no Nome e na Descrição/Foco da Campanha fornecidos acima! Adapte a recepção do lead e seu pitch inicial exatamente conforme as diretrizes descritas na Descrição/Foco da Campanha!
* RECONHECIMENTO DE RETORNO (Para cliente recorrente — modo padrão): Se o CLIENTE RECORRENTE for "Sim", NÃO se apresente novamente (não diga "Eu sou o/a {nome_agente}, assistente da..."). Cumprimente-o pessoalmente (ex: "Olá, {lead_nome}! Que bom falar com você novamente! Como posso ajudar hoje?") e vá direto ao ponto sem repetir apresentações formais.
* Seu tom geral deve ser: {tom_voz}

=== SUA MISSÃO ===
{missao}

=== INSTRUÇÕES ADICIONAIS ===
{instrucoes_adicionais}

=== NICHO DE ATUAÇÃO ===
Você atua no nicho: {nicho.upper()}

=== SUA MISSÃO DE TRIAGEM PERSONALIZADA ===
Sua missão secundária é realizar o pré-atendimento (triagem) dos leads coletando os dados definidos pelo administrador.
Você deve coletar APENAS UM DADO POR VEZ de forma extremamente amigável e conversacional. Não bombardeie o cliente com várias perguntas de uma vez só!

=== CAMPOS QUE VOCÊ PRECISA COLETAR (PENDENTES) ===
{campos_pendentes}

=== DADOS QUE JÁ FORAM COLETADOS (MEMÓRIA DO SISTEMA) ===
{campos_coletados}

=== CONTEXTO ATUAL ===
{ctx['contexto_tempo']}
INTENÇÃO DETECTADA: {ctx['intencao']}
ESTÁGIO DO LEAD NO FUNIL: {ctx['stage']}
SENTIMENTO DO CLIENTE: {ctx['sentimento'].upper()}
{"[ALERTA: O usuário parece frustrado ou irritado. Seja extra empático, calmo e prestativo.]" if ctx['sentimento'] == 'negativo' else ""}

=== BASE DE CONHECIMENTO ===
{secoes_conhecimento}

=== REGRAS DE ATENDIMENTO ===
{regras_str}

=== REGRA DE OURO CRÍTICA: SALVAR DADOS NO BANCO (MANDATÓRIO) ===
Sempre que o cliente fornecer, alterar ou confirmar qualquer dado dele na mensagem dele, você DEVE OBRIGATORIAMENTE anexar a tag de dados técnica correspondente no final da sua resposta, na última linha de texto, separada por um espaço ou quebra de linha. Se você não incluir a tag técnica exata, o banco de dados não salvará a informação e o dado será perdido!

FORMATO DAS TAGS (SEMPRE EM UMA NOVA LINHA NO FINAL DA RESPOSTA):
[ATUALIZAR_LEAD: chave=valor]

Exemplos de Mapeamento:
- Se ele informou o Nome Completo -> [ATUALIZAR_LEAD: nome_completo=Carlos da Silva]
- Se ele informou a Idade -> [ATUALIZAR_LEAD: idade=28 anos]
- Se ele informou o Objetivo -> [ATUALIZAR_LEAD: objetivo=Ganho de Massa]
- Se ele informou a Frequência -> [ATUALIZAR_LEAD: frequencia=3 a 4 dias]

=== CONCLUSÃO DE TRIAGEM ===
ASSIM QUE CONCLUIR A COLETA DOS DADOS OBRIGATÓRIOS (ou se todos os campos que falta coletar estiverem preenchidos):
- Informe educadamente que os dados foram coletados e que você está repassando para o time que entrará em contato em instantes.
- Você DEVE obrigatoriamente incluir a tag invisível: [SOLICITAR_HUMANO: motivo=Triagem concluída - pronto para atendimento]
- A inclusão dessa tag suspenderá as respostas automáticas do robô para que a equipe continue o atendimento humanamente.

=== FLUXO DE TRANSBORDO (ATENDIMENTO HUMANO DE EMERGÊNCIA) ===
Você deve detectar quando o cliente precisa de um humano urgente (frustração extrema, pedido explícito ou dúvida muito complexa).
Nesses casos, adicione a tag [SUGERIR_TRANSBORDO] no final.
Se o cliente confirmar: use a tag [CONFIRMAR_TRANSBORDO].
Se o cliente recusar: use a tag [CANCELAR_TRANSBORDO].
"""

    def _montar_conhecimento(self, config: dict) -> str:
        secoes_conhecimento = ""
        conhecimento_raw = config.get('conhecimento', [])

        if isinstance(conhecimento_raw, list):
            for item in conhecimento_raw:
                if isinstance(item, dict):
                    titulo = item.get('categoria') or item.get('titulo') or 'Informação'
                    conteudo = item.get('conteudo') or item.get('resposta') or ''
                    if conteudo:
                        secoes_conhecimento += f"\n=== {titulo.upper()} ===\n{conteudo}\n"
                elif isinstance(item, str) and item:
                    secoes_conhecimento += f"- {item}\n"
        elif isinstance(conhecimento_raw, dict):
            for titulo, conteudo in conhecimento_raw.items():
                if not conteudo: continue
                secoes_conhecimento += f"\n=== {titulo.replace('_', ' ').upper()} ===\n"
                if isinstance(conteudo, list):
                    for subitem in conteudo:
                        secoes_conhecimento += f"- {subitem}\n"
                else:
                    secoes_conhecimento += f"{conteudo}\n"

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

        horarios = config.get('horarios', {})
        if horarios:
            secoes_conhecimento += "\n=== HORÁRIO DE FUNCIONAMENTO ===\n"
            secoes_conhecimento += f"- Segunda a Sexta: {horarios.get('semana', 'Não informado')}\n"
            secoes_conhecimento += f"- Sábados: {horarios.get('sabado', 'Não informado')}\n"
            secoes_conhecimento += f"- Domingos: {horarios.get('domingo', 'Fechado')}\n"
            secoes_conhecimento += f"- Feriados: {horarios.get('feriado', 'Fechado')}\n"

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

        if not secoes_conhecimento and 'planos' in config:
            planos = config.get('planos', {})
            secoes_conhecimento += f"=== PLANOS DA ACADEMIA ===\n{planos}\n"

        faq = config.get('faq', [])
        if isinstance(faq, list) and faq:
            secoes_conhecimento += "\n=== PERGUNTAS FREQUENTES (FAQ) ===\n"
            for item in faq:
                if isinstance(item, dict):
                    pergunta = item.get('pergunta') or item.get('question')
                    resposta = item.get('resposta') or item.get('answer')
                    if pergunta and resposta:
                        secoes_conhecimento += f"P: {pergunta}\nR: {resposta}\n\n"

        return secoes_conhecimento

    def _montar_regras(self, config: dict) -> str:
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
            regras_seguranca = [
                "Nunca inventar informações que não estão listadas na base de conhecimento (como preços, horários, planos, professores ou modalidades).",
                "Se o usuário perguntar sobre professores, equipe, modalidades ou grade de aulas e essa informação não estiver descrita explicitamente na base de conhecimento, diga educadamente que não sabe e ofereça encaminhar para o atendimento humano."
            ]
            for r_seg in regras_seguranca:
                if not any(r_seg[:30] in r for r in regras):
                    regras.append(r_seg)
        return "\n".join([f"{i+1}. {regra}" for i, regra in enumerate(regras)])
