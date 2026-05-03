def classificar_intencao(texto: str) -> str:
    texto = texto.lower()
    if any(p in texto for p in ["preço", "preco", "valor", "quanto", "custa", "mensalidade"]):
        return "preco"
    if any(p in texto for p in ["horário", "horario", "hora", "abre", "fecha", "funciona"]):
        return "horario"
    if any(p in texto for p in ["aula", "spinning", "zumba", "funcional", "fitdance", "musculação", "musculacao"]):
        return "aulas"
    if any(p in texto for p in ["visitar", "conhecer", "ir", "vir", "aparecer"]):
        return "visita"
    if any(p in texto for p in ["plano", "modalidade", "contrato"]):
        return "plano"
    return "duvida"

def calcular_stage(stage_atual: str, intencao: str) -> str:
    """
    Atualiza o funil de vendas baseado na intenção.
    Estágios: novo -> curioso -> interessado -> (quente/agendado tratado separadamente)
    """
    progressao = {
        "novo": {
            "preco": "curioso",
            "horario": "curioso",
            "aulas": "curioso",
            "plano": "curioso",
            "visita": "interessado"
        },
        "curioso": {
            "visita": "interessado",
            "plano": "interessado",
        },
        "interessado": {}
    }
    return progressao.get(stage_atual, {}).get(intencao, stage_atual)
