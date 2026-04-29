from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perguntar(mensagem_usuario, contexto_sistema, historico=None):
    if historico is None:
        historico = []
        
    mensagens = [{"role": "system", "content": contexto_sistema}]
    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": mensagem_usuario})
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=mensagens
    )
    return response.choices[0].message.content