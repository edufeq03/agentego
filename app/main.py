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
    # Recupera a última mensagem que o bot enviou para esse número
    ultima_msg = historico_conversas.get(telefone)
    
    # Processa a nova mensagem passando o contexto anterior
    resposta = processar_mensagem(mensagem, ultima_mensagem=ultima_msg)
    
    # Salva a nova resposta na memória para a próxima iteração
    historico_conversas[telefone] = resposta

    print(f"Mensagem recebida de {telefone}: {mensagem}")
    print(f"Resposta gerada (IA Livre): {resposta}")

    enviar_whatsapp(telefone, resposta)

    return {"status": "ok", "resposta": resposta}