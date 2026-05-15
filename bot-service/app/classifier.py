from app.openai_client import perguntar

def analisar_sentimento_ia(texto: str) -> str:
    """
    Usa IA para classificar o humor do cliente.
    Retorna: 'positivo', 'neutro' ou 'negativo'.
    """
    prompt = """
    Analise o sentimento da mensagem abaixo de um cliente de uma academia/serviço.
    Responda APENAS com uma das palavras: 'positivo', 'neutro' ou 'negativo'.
    
    Exemplos:
    - "Achei um absurdo essa demora" -> negativo
    - "Queria saber o preço" -> neutro
    - "Muito obrigado pela atenção, adorei" -> positivo
    - "Que porcaria de atendimento" -> negativo
    """
    try:
        res, t_in, t_out = perguntar(texto, prompt)
        res = res.lower().strip()
        sentimento = "neutro"
        if "negativo" in res: sentimento = "negativo"
        elif "positivo" in res: sentimento = "positivo"
        return sentimento, t_in, t_out
    except:
        return "neutro", 0, 0

def classificar_intencao(texto: str) -> str:
    texto = texto.lower()
    if any(p in texto for p in ["preço", "preco", "valor", "quanto", "custa", "mensalidade", "orçamento", "orcamento"]):
        return "preco"
    if any(p in texto for p in ["horário", "horario", "hora", "abre", "fecha", "funciona", "agendar", "agenda"]):
        return "horario"
    if any(p in texto for p in ["aula", "serviço", "servico", "procedimento", "imóvel", "imovel", "casa", "apartamento", "produto"]):
        return "servicos"
    if any(p in texto for p in ["visitar", "conhecer", "ir", "vir", "aparecer"]):
        return "visita"
    if any(p in texto for p in ["plano", "modalidade", "contrato", "pacote", "assinatura"]):
        return "plano"
    return "duvida"

def calcular_stage(stage_atual: str, intencao: str, etapas_disponiveis: list = None) -> str:
    """
    Atualiza o funil de vendas baseado na intenção.
    Se etapas_disponiveis for fornecido, tenta mapear para uma das etapas da lista.
    """
    # Mapa de progressão base (simplificado)
    progressao = {
        "novo": {
            "preco": "curioso",
            "horario": "curioso",
            "servicos": "curioso",
            "plano": "curioso",
            "visita": "interessado"
        },
        "curioso": {
            "visita": "interessado",
            "plano": "interessado",
        },
        "interessado": {
            "visita": "agendado"
        }
    }
    
    # Se não temos etapas customizadas, usa o padrão
    if not etapas_disponiveis:
        return progressao.get(stage_atual.lower(), {}).get(intencao, stage_atual)
        
    # Tenta encontrar o próximo estágio lógico
    proximo_simplificado = progressao.get(stage_atual.lower(), {}).get(intencao)
    
    if not proximo_simplificado:
        return stage_atual
        
    # Mapeia o proximo_simplificado para uma das etapas reais da empresa
    for etapa_real in etapas_disponiveis:
        if proximo_simplificado in etapa_real.lower():
            return etapa_real
            
    return stage_atual
