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

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "online", "message": "Agente Academia está rodando!"}

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
        if "@s.whatsapp.net" in remote_jid:
            telefone = remote_jid.split("@")[0]
            
        # Ignora mensagens enviadas por você mesmo (evita loop infinito)
        if event_data.get("key", {}).get("fromMe") == True:
            return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_bot"}
            
        # Pega o texto ou áudio da mensagem
        msg_obj = event_data.get("message", {})
        message_type = event_data.get("messageType", "")

        if "conversation" in msg_obj:
            mensagem = msg_obj["conversation"]
        elif "extendedTextMessage" in msg_obj:
            mensagem = msg_obj["extendedTextMessage"].get("text", "")
        elif message_type == "audioMessage" or "audioMessage" in msg_obj:
            # Em diferentes versões da Evolution, o base64 pode vir na raiz do data ou dentro de message
            base64_audio = msg_obj.get("base64") or event_data.get("base64")
            
            if base64_audio:
                import base64
                import tempfile
                import os
                from app.openai_client import transcrever_audio
                
                # Se o base64 vier com cabeçalho (ex: data:audio/ogg;base64,UklGR...), cortamos fora a primeira parte
                if "," in base64_audio:
                    base64_audio = base64_audio.split(",")[1]
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
                    temp_audio.write(base64.b64decode(base64_audio))
                    temp_path = temp_audio.name
                
                try:
                    mensagem = transcrever_audio(temp_path)
                    logger.info(f"[{telefone}] Áudio transcrito com sucesso: '{mensagem}'")
                except Exception as e:
                    logger.error(f"Erro ao transcrever áudio: {e}")
                    return {"status": "erro", "motivo": "falha_transcricao"}
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                logger.warning(f"[{telefone}] Áudio recebido, mas opção 'base64' não está ativada no Webhook da Evolution (ou estrutura JSON desconhecida).")
                return {"status": "ignorado", "motivo": "audio_sem_base64"}
            
    # Se ainda assim não tiver mensagem, retorna ignorado
    if not mensagem:
        return {"status": "ignorado", "motivo": "sem_texto"}

    from app.database import obter_conversa, salvar_mensagem
    
    # Salvar a mensagem recebida no banco
    conversa_id = obter_conversa(telefone)
    salvar_mensagem(conversa_id, "usuario", mensagem)

    # Recupera o histórico completo desse número (ou cria uma lista vazia)
    historico = historico_conversas.get(telefone, [])
    
    # Envia o status de "Escrevendo..." para a Evolution API
    from app.whatsapp import simular_digitacao
    simular_digitacao(telefone)
    
    # Processa a nova mensagem passando o histórico (o tempo que a IA leva para pensar será o tempo de "Escrevendo...")
    resposta = processar_mensagem(mensagem, historico=historico)
    
    # Salvar a resposta gerada no banco
    salvar_mensagem(conversa_id, "agente", resposta)
    
    # Adiciona a pergunta do usuário e a resposta da IA no histórico
    historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})
    
    # Mantém apenas as últimas 6 mensagens (3 interações completas) para economizar tokens
    historico_conversas[telefone] = historico[-6:]

    # Log limpo em uma única linha para auditoria
    logger.info(f"[{telefone}] Cliente: '{mensagem}' -> IA: '{resposta}'")

    import asyncio
    # Quebra a resposta em parágrafos (remove espaços extras) e envia como mensagens separadas
    paragrafos = [p.strip() for p in resposta.split('\n') if p.strip()]
    
    for i, paragrafo in enumerate(paragrafos):
        if i > 0:
            # Reenvia o status de digitação para cada nova mensagem quebrada
            simular_digitacao(telefone)
            # Calcula um tempo de espera proporcional ao tamanho do texto (mínimo 1s, máximo 3s)
            tempo_espera = max(1.0, min(3.0, len(paragrafo) / 40.0))
            await asyncio.sleep(tempo_espera)
            
        enviar_whatsapp(telefone, paragrafo)

    return {"status": "ok", "resposta": resposta}

@app.get("/conversas")
def listar_conversas():
    from app.database import listar_conversas_com_mensagens
    return {"conversas": listar_conversas_com_mensagens()}