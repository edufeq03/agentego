from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from app.agent import processar_mensagem
from app.whatsapp import enviar_whatsapp

# Memória temporária em RAM (Dicionário: Telefone -> Última Mensagem)
historico_conversas = {}

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # Formato simples (Testes manuais)
    mensagem = data.get("message")
    telefone = data.get("phone")

    # Formato real da Evolution API (Quando o WhatsApp manda a mensagem direto pra cá)
    if not mensagem and "data" in data:
        event_data = data["data"]
        
        # Ignora mensagens enviadas por você mesmo (evita loop infinito)
        if event_data.get("key", {}).get("fromMe") == True:
            return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_bot"}
            
        # Pega o número do remetente
        remote_jid = event_data.get("key", {}).get("remoteJid", "")
        if "@s.whatsapp.net" in remote_jid:
            telefone = remote_jid.split("@")[0]
            
        # Pega o texto da mensagem
        msg_obj = event_data.get("message", {})
        if "conversation" in msg_obj:
            mensagem = msg_obj["conversation"]
        elif "extendedTextMessage" in msg_obj:
            mensagem = msg_obj["extendedTextMessage"].get("text", "")
            
    # Se ainda assim não tiver mensagem, retorna ignorado
    # Recupera o histórico completo desse número (ou cria uma lista vazia)
    historico = historico_conversas.get(telefone, [])
    
    # Processa a nova mensagem passando o histórico
    resposta = processar_mensagem(mensagem, historico=historico)
    
    # Adiciona a pergunta do usuário e a resposta da IA no histórico
    historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})
    
    # Mantém apenas as últimas 6 mensagens (3 interações completas) para economizar tokens
    historico_conversas[telefone] = historico[-6:]

    print(f"Mensagem recebida de {telefone}: {mensagem}")
    print(f"Resposta gerada (IA Livre): {resposta}")

    enviar_whatsapp(telefone, resposta)

    return {"status": "ok", "resposta": resposta}