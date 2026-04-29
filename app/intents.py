from app.openai_client import perguntar

def classificar_intencao(mensagem):
    prompt = f"""
    Classifique a intenção:

    "{mensagem}"

    Responda apenas:
    HORARIO, PRECO ou OUTRO
    """
    
    return perguntar(prompt).strip().upper()