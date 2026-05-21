from app.agents.base_agent import BaseAgent
from app.openai_client import perguntar

class EspecialistaGenerico(BaseAgent):
    nome = "EspecialistaGenerico"

    def processar(self, mensagem: str, contexto: dict, historico: list) -> tuple[str, int, int]:
        prompt = self._montar_prompt(contexto)
        openai_hist = self.montar_historico_openai(historico)
        return perguntar(mensagem, prompt, openai_hist)

    def _montar_prompt(self, ctx: dict) -> str:
        config = ctx["config"]

        nome_agente = ctx["nome_agente"]
        nome_empresa = ctx["nome_empresa"]
        cargo = config.get('cargo_agente') or config.get('identidade', {}).get('cargo') or 'Assistente Virtual'
        missao = config.get('missao') or config.get('identidade', {}).get('missao') or 'Auxiliar clientes com clareza e eficiência.'
        tom_voz = config.get('tom_voz') or config.get('identidade', {}).get('tom_voz') or 'Amigável e profissional.'
        instrucoes_adicionais = config.get('prompt_sistema') or config.get('instrucoes') or ''
        nicho = ctx["nicho"]

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

=== FLUXO DE TRANSBORDO (ATENDIMENTO HUMANO) ===
Você deve detectar quando o cliente precisa de um humano (frustração, pedido explícito ou dúvida complexa).
Nesses casos:
1. Responda com empatia.
2. Pergunte se ele deseja falar com um atendente humano.
3. Adicione a tag [SUGERIR_TRANSBORDO] no final.

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
            secoes_conhecimento += f"- Domingos e Feriados: {horarios.get('domingo', 'Fechado')}\n"

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
