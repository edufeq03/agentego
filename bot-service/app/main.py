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
from app.agent import processar_mensagem, processar_confirmacao_transbordo
from app.whatsapp import enviar_whatsapp
from app.database import (
    obter_conversa, salvar_mensagem, listar_conversas_com_mensagens,
    obter_status_transbordo, marcar_aguardando_confirmacao,
    marcar_pausado, limpar_transbordo
)

def limpar_tags(texto: str) -> str:
    """Remove as tags internas antes de enviar para o cliente."""
    for tag in ["[SUGERIR_TRANSBORDO]", "[CONFIRMAR_TRANSBORDO]", "[CANCELAR_TRANSBORDO]"]:
        texto = texto.replace(tag, "").strip()
    return texto

# Memória temporária em RAM (Dicionário: Telefone -> Última Mensagem)
historico_conversas = {}

app = FastAPI()

@app.on_event("startup")
def on_startup():
    from app.database import init_db
    init_db()

@app.get("/")
def health_check():
    return {"status": "online", "message": "Agente Academia está rodando!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # Formato simples (Testes manuais)
    mensagem = data.get("message")
    telefone = data.get("phone")
    cliente_enviou_audio = False

    # Formato real da Evolution API (Quando o WhatsApp manda a mensagem direto pra cá)
    if not mensagem and "data" in data:
        event_data = data["data"]
        
        # Pega o número do remetente
        remote_jid = event_data.get("key", {}).get("remoteJid", "")
        if "@s.whatsapp.net" in remote_jid:
            telefone = remote_jid.split("@")[0]
            
        # Pega o texto ou áudio da mensagem primeiro para podermos ler comandos
        msg_obj = event_data.get("message", {})
        message_type = event_data.get("messageType", "")

        if "conversation" in msg_obj:
            mensagem = msg_obj["conversation"]
        elif "extendedTextMessage" in msg_obj:
            mensagem = msg_obj["extendedTextMessage"].get("text", "")

        # Trata mensagens enviadas por você mesmo (evita loop infinito)
        if event_data.get("key", {}).get("fromMe") == True:
            # Se você (humano) digitar /reativar na conversa com o cliente, o robô volta
            if mensagem and mensagem.strip().lower() == "/reativar":
                limpar_transbordo(telefone)
                enviar_whatsapp(telefone, "🤖 *Atendimento Automático Reativado*.")
                logger.info(f"[{telefone}] Robô reativado pelo corretor via chat (/reativar).")
                return {"status": "ok", "mensagem": "reativado_via_chat"}
                
            return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_bot"}
        elif message_type == "audioMessage" or "audioMessage" in msg_obj:
            cliente_enviou_audio = True
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

    # ── Verificar status de transbordo ────────────────────────────────────────
    status_transbordo = obter_status_transbordo(telefone)

    # Número completamente pausado — não responde nada
    if status_transbordo == "pausado":
        logger.info(f"[{telefone}] Número pausado (transbordo ativo). Mensagem ignorada.")
        return {"status": "pausado", "motivo": "transbordo_ativo"}
    
    # Salvar a mensagem recebida no banco
    conversa_id = obter_conversa(telefone)
    salvar_mensagem(conversa_id, "usuario", mensagem)

    # Recupera o histórico completo desse número (ou cria uma lista vazia)
    historico = historico_conversas.get(telefone, [])
    
    # Envia o status para a Evolution API
    from app.whatsapp import simular_digitacao, simular_gravacao_audio, enviar_audio_whatsapp
    
    if cliente_enviou_audio:
        simular_gravacao_audio(telefone)
    else:
        simular_digitacao(telefone)
    
    # ── Número aguardando confirmação de transbordo ───────────────────────────
    if status_transbordo == "aguardando":
        resposta_raw = processar_confirmacao_transbordo(mensagem, historico=historico)
        if "[CONFIRMAR_TRANSBORDO]" in resposta_raw:
            marcar_pausado(telefone)
            logger.info(f"[{telefone}] Transbordo CONFIRMADO. Robô pausado.")
        elif "[CANCELAR_TRANSBORDO]" in resposta_raw:
            limpar_transbordo(telefone)
            logger.info(f"[{telefone}] Transbordo CANCELADO. Robô retomando.")
            historico.append({"role": "user", "content": mensagem})
            historico.append({"role": "assistant", "content": limpar_tags(resposta_raw)})
        else:
            historico.append({"role": "user", "content": mensagem})
            historico.append({"role": "assistant", "content": limpar_tags(resposta_raw)})
    else:
        # ── Atendimento normal ────────────────────────────────────────────────────
        resposta_raw = processar_mensagem(mensagem, historico=historico)
        if "[SUGERIR_TRANSBORDO]" in resposta_raw:
            marcar_aguardando_confirmacao(telefone)
            logger.info(f"[{telefone}] Transbordo SUGERIDO. Aguardando confirmação do cliente.")
        
        historico.append({"role": "user", "content": mensagem})
        historico.append({"role": "assistant", "content": limpar_tags(resposta_raw)})
    
    resposta = limpar_tags(resposta_raw)
    
    # Salvar a resposta final gerada no banco
    salvar_mensagem(conversa_id, "agente", resposta)
    
    # Mantém apenas as últimas 6 mensagens (3 interações completas) para economizar tokens
    historico_conversas[telefone] = historico[-6:]

    # Log limpo em uma única linha para auditoria
    logger.info(f"[{telefone}] Cliente: '{mensagem}' -> IA: '{resposta}'")

    import asyncio
    
    if cliente_enviou_audio:
        import os
        import tempfile
        from app.openai_client import gerar_audio
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_out:
            caminho_audio_resposta = temp_out.name
            
        try:
            gerar_audio(resposta, caminho_audio_resposta)
            enviar_audio_whatsapp(telefone, caminho_audio_resposta)
        except Exception as e:
            logger.error(f"Erro ao gerar/enviar audio de resposta: {e}")
            # Fallback de segurança: se a geração de áudio falhar, manda texto.
            enviar_whatsapp(telefone, resposta) 
        finally:
            if os.path.exists(caminho_audio_resposta):
                os.remove(caminho_audio_resposta)
    else:
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
    return {"conversas": listar_conversas_com_mensagens()}

@app.delete("/transbordo/{telefone}")
def reativar_robo(telefone: str):
    """Endpoint para a recepcionista reativar o robô manualmente (ex.: n8n, Postman)."""
    limpar_transbordo(telefone)
    logger.info(f"[{telefone}] Robô reativado manualmente via API.")
    return {"status": "ok", "mensagem": f"Robô reativado para {telefone}"}