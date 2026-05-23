from app.agents.base_agent import BaseAgent
from app.openai_client import perguntar

class EspecialistaContabilidade(BaseAgent):
    nome = "EspecialistaContabilidade"

    def processar(self, mensagem: str, contexto: dict, historico: list) -> tuple[str, int, int]:
        prompt = self._montar_prompt(contexto)
        openai_hist = self.montar_historico_openai(historico)
        temperature = contexto.get("config", {}).get("openai_temperature", 0.2)
        return perguntar(mensagem, prompt, openai_hist, temperature=temperature)

    def _montar_prompt(self, ctx: dict) -> str:
        config = ctx["config"]

        nome_agente = ctx["nome_agente"]
        nome_empresa = ctx["nome_empresa"]
        cargo = config.get('cargo_agente') or config.get('identidade', {}).get('cargo') or 'Assistente Virtual'
        missao = config.get('missao') or config.get('identidade', {}).get('missao') or 'Auxiliar clientes com clareza e eficiência.'
        tom_voz = config.get('tom_voz') or config.get('identidade', {}).get('tom_voz') or 'Amigável e profissional.'
        instrucoes_adicionais = config.get('prompt_sistema') or config.get('instrucoes') or ''

        def limpar_placeholders(texto):
            if not texto: return ""
            texto = texto.replace("[NOME_DA_ACADEMIA]", nome_empresa)
            texto = texto.replace("[NOME_DA_EMPRESA]", nome_empresa)
            texto = texto.replace("[NOME_DO_AGENTE]", nome_agente)
            return texto

        missao = limpar_placeholders(missao)
        tom_voz = limpar_placeholders(tom_voz)
        instrucoes_adicionais = limpar_placeholders(instrucoes_adicionais)

        # Regras de comportamento
        regras = config.get('regras_comportamento') or config.get('regras') or [
            "Identificar a necessidade do usuário com clareza.",
            "Ser direto, objetivo e empático.",
            "Nunca inventar informações não listadas na base de conhecimento.",
            "Se o usuário perguntar algo não listado, oferecer atendimento humano.",
            "Utilizar emojis com moderação.",
        ]
        regras_str = "\n".join([f"{i+1}. {r}" for i, r in enumerate(regras)])

        # Montar base de conhecimento e documentos legais
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

        docs = ctx.get("documentos_legais", [])
        if docs:
            secoes_conhecimento += "\n=== BASE LEGAL E DOCUMENTOS ===\n"
            secoes_conhecimento += "Use as informações abaixo para responder dúvidas técnicas:\n"
            for doc in docs:
                titulo = doc.get("titulo") or doc.get("categoria") or "Documento"
                conteudo = doc.get("conteudo") or doc.get("resposta") or ""
                secoes_conhecimento += f"\n- {titulo}:\n{conteudo}\n"

        return f"""
Você é {nome_agente}, {cargo} da {nome_empresa}.

=== SUA MISSÃO ===
{missao}

=== SEU TOM DE VOZ ===
{tom_voz}

=== INSTRUÇÕES ADICIONAIS ===
{instrucoes_adicionais}

=== NICHO DE ATUAÇÃO ===
Você atua no nicho: CONTABILIDADE
[IMPORTANTE: Você é um assistente de contabilidade. Seja preciso com termos técnicos e use a base legal fornecida.]

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
