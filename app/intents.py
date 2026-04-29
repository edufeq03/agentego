from app.openai_client import perguntar
from app.responses import RESPOSTAS

def classificar_intencao(mensagem):
    lista_intencoes = ", ".join(RESPOSTAS.keys())
    
    prompt = f"""
    Sua tarefa é classificar a intenção da mensagem do usuário.
    
    Lista de intenções válidas: [{lista_intencoes}, OUTRO]

    Mensagem do usuário: "{mensagem}"

    Responda APENAS com o nome da intenção (exatamente como está na lista em maiúsculo). Se não se encaixar em nenhuma, responda OUTRO.
    """
    
    return perguntar(prompt).strip().upper()