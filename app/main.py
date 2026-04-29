from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, Request

# Configuração de Log limpo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)
from app.agent import processar_mensagem
from app.whatsapp import enviar_whatsapp

# Memória temporária em RAM (Dicionário: Telefone -> Última Mensagem)
historico_conversas = {}
# Lista de clientes que estão sendo atendidos por humano
clientes_pausados = set()

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
        
        # Pega o número do remetente
        remote_jid = event_data.get("key", {}).get("remoteJid", "")
        telefone_origem = ""
        if "@s.whatsapp.net" in remote_jid:
            telefone_origem = remote_jid.split("@")[0]
            telefone = telefone_origem
            
        # Ignora mensagens enviadas por você mesmo (evita loop infinito)
        if event_data.get("key", {}).get("fromMe") == True:
            msg_obj = event_data.get("message", {})
            msg_texto = msg_obj.get("conversation") or msg_obj.get("extendedTextMessage", {}).get("text", "")
            
            # Se a recepcionista digitou /voltar, reativa o robô
            if msg_texto.strip().lower() in ["/voltar", "#voltar"]:
                if telefone_origem in clientes_pausados:
                    clientes_pausados.remove(telefone_origem)
                    logger.info(f"[{telefone_origem}] Bot REATIVADO pela recepcionista.")
                return {"status": "reativado"}
                
            return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_bot_ou_humano"}
            
        # Pega o texto da mensagem
        msg_obj = event_data.get("message", {})
        if "conversation" in msg_obj:
            mensagem = msg_obj["conversation"]
        elif "extendedTextMessage" in msg_obj:
            mensagem = msg_obj["extendedTextMessage"].get("text", "")
            
    # Se ainda assim não tiver mensagem, retorna ignorado
    if not mensagem:
        return {"status": "ignorado", "motivo": "sem_texto"}

    # Se o bot estiver pausado para esse cliente (transbordo ativo), ignora
    if telefone in clientes_pausados:
        logger.info(f"[{telefone}] Mensagem ignorada (Bot pausado para atendimento humano)")
        return {"status": "ignorado", "motivo": "pausado_para_humano"}

    # Recupera o histórico completo desse número (ou cria uma lista vazia)
    historico = historico_conversas.get(telefone, [])
    
    # Envia o status de "Escrevendo..." para a Evolution API
    from app.whatsapp import simular_digitacao
    simular_digitacao(telefone)
    
    # Processa a nova mensagem passando o histórico (o tempo que a IA leva para pensar será o tempo de "Escrevendo...")
    resposta = processar_mensagem(mensagem, historico=historico)
    
    # Verifica se a IA acionou o Transbordo
    if "[TRANSBORDO]" in resposta:
        clientes_pausados.add(telefone)
        resposta = "Só um instante, vou chamar um dos nossos recepcionistas para continuar o seu atendimento! 🙋‍♀️"
        logger.info(f"[{telefone}] TRANSBORDO ACIONADO. Bot pausado.")
    
    # Adiciona a pergunta do usuário e a resposta da IA no histórico
    historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})
    
    # Mantém apenas as últimas 6 mensagens (3 interações completas) para economizar tokens
    historico_conversas[telefone] = historico[-6:]

    # Log limpo em uma única linha para auditoria
    logger.info(f"[{telefone}] Cliente: '{mensagem}' -> IA: '{resposta}'")

    enviar_whatsapp(telefone, resposta)

    return {"status": "ok", "resposta": resposta}