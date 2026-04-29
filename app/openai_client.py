from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perguntar(mensagem_usuario, contexto_sistema):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": contexto_sistema},
            {"role": "user", "content": mensagem_usuario}
        ]
    )
    return response.choices[0].message.content