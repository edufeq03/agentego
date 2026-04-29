from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from app.intents import classificar_intencao
from app.responses import gerar_resposta
from app.whatsapp import enviar_whatsapp

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    mensagem = data.get("message")
    telefone = data.get("phone")

    intencao = classificar_intencao(mensagem)
    resposta = gerar_resposta(intencao)

    print(f"Mensagem recebida: {mensagem}")
    print(f"Intenção classificada: {intencao}")
    print(f"Resposta gerada: {resposta}")

    enviar_whatsapp(telefone, resposta)

    return {"status": "ok", "resposta": resposta}