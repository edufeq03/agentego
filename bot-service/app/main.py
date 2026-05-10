from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, Request, HTTPException
import asyncio

# Configuração de Log limpo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)

from app.database import get_db, SessionLocal, Empresa, init_db
from app.pipeline import processar_webhook
from app.whatsapp import enviar_whatsapp, simular_digitacao, simular_gravacao_audio, enviar_audio_whatsapp
from app.openai_client import transcrever_audio, gerar_audio
from app.buffer import adicionar_mensagem
import os
import tempfile
import base64

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Para desenvolvimento. Em prod, restrinja ao domínio do dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from app.dashboard_api import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.reports import enviar_relatorio_semanal_empresa
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone('America/Sao_Paulo'))

async def tarefa_relatorio_semanal():
    logger.info("Iniciando disparo automático de relatórios semanais...")
    db = SessionLocal()
    try:
        empresas = db.query(Empresa).filter(Empresa.ativo == True, Empresa.telefone_proprietario.isnot(None)).all()
        for empresa in empresas:
            await enviar_relatorio_semanal_empresa(db, empresa)
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    # Agenda para toda Segunda-feira às 09:00 AM
    scheduler.add_job(tarefa_relatorio_semanal, 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.start()
    logger.info("Scheduler iniciado: Relatórios semanais agendados para Segundas às 09:00.")

@app.get("/")

def health_check():
    return {"status": "online", "message": "AtendIA (SaaS) está rodando!"}

async def processar_pipeline_callback(empresa_simplificada, telefone: str, texto_combinado: str, cliente_enviou_audio: bool = False):
    """
    Callback disparada pelo buffer de mensagens após o tempo de debounce.
    """
    db = SessionLocal()
    try:
        # Recupera a empresa com a sessão atual
        empresa = db.query(Empresa).filter(Empresa.id == empresa_simplificada.id).first()
        if not empresa:
            return

        # Simular status de "digitando" ou "gravando" na Evolution
        if cliente_enviou_audio:
            simular_gravacao_audio(telefone, empresa.evolution_instance)
        else:
            simular_digitacao(telefone, empresa.evolution_instance)

        # Processar no Pipeline Central
        resultado = processar_webhook(empresa, telefone, texto_combinado)
        
        if resultado["status"] == "pausado":
            logger.info(f"[{telefone}] Número pausado (transbordo ativo). Mensagem ignorada.")
            return

        resposta = resultado["resposta"]
        logger.info(f"[{telefone}] Cliente: '{texto_combinado}' -> IA: '{resposta}'")

        # Enviar Resposta via Evolution API
        if cliente_enviou_audio:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_out:
                caminho_audio_resposta = temp_out.name
            try:
                gerar_audio(resposta, caminho_audio_resposta)
                enviar_audio_whatsapp(telefone, caminho_audio_resposta, empresa.evolution_instance)
            except Exception as e:
                logger.error(f"Erro ao gerar/enviar audio de resposta: {e}")
                enviar_whatsapp(telefone, resposta, empresa.evolution_instance) 
            finally:
                if os.path.exists(caminho_audio_resposta):
                    os.remove(caminho_audio_resposta)
        else:
            paragrafos = [p.strip() for p in resposta.split('\n') if p.strip()]
            for i, paragrafo in enumerate(paragrafos):
                if i > 0:
                    simular_digitacao(telefone, empresa.evolution_instance)
                    tempo_espera = max(1.0, min(3.0, len(paragrafo) / 40.0))
                    await asyncio.sleep(tempo_espera)
                enviar_whatsapp(telefone, paragrafo, empresa.evolution_instance)

    except Exception as e:
        logger.error(f"Erro no processamento do pipeline em background: {e}")
    finally:
        db.close()


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    db = SessionLocal()
    try:
        logger.info(f"--- WEBHOOK RECEBIDO (Token: {token}) ---")
        data = await request.json()
        import json
        logger.info(f"RAW DATA: {json.dumps(data)}")

        # 1. Identificar Empresa pelo token
        empresa = db.query(Empresa).filter(Empresa.webhook_token == token, Empresa.ativo == True).first()
        if not empresa:
            logger.warning(f"Webhook recebido com token INVÁLIDO ou empresa inativa: {token}")
            return {"status": "erro", "motivo": "token_invalido"}

        # 2. Extrair dados da Evolution API
        mensagem = data.get("message")
        telefone = data.get("phone")
        cliente_enviou_audio = False

        # Se a mensagem vier como objeto (Evolution v2 ou simulação)
        if isinstance(mensagem, dict):
            msg_obj = mensagem
            if "conversation" in msg_obj:
                mensagem = msg_obj["conversation"]
            elif "extendedTextMessage" in msg_obj:
                mensagem = msg_obj["extendedTextMessage"].get("text", "")
            else:
                mensagem = None

        if not mensagem and "data" in data:
            event_data = data["data"]
            
            remote_jid = event_data.get("key", {}).get("remoteJid", "")
            if "@s.whatsapp.net" in remote_jid:
                telefone = remote_jid.split("@")[0]
                
            msg_obj = event_data.get("message", {})
            message_type = event_data.get("messageType", "")

            if "conversation" in msg_obj:
                mensagem = msg_obj["conversation"]
            elif "extendedTextMessage" in msg_obj:
                mensagem = msg_obj["extendedTextMessage"].get("text", "")

            # Evitar loop de si mesmo
            if event_data.get("key", {}).get("fromMe") == True:
                if mensagem and mensagem.strip().lower() == "/reativar":
                    from app.pipeline import atualizar_status_transbordo
                    atualizar_status_transbordo(db, empresa.id, telefone, None)
                    enviar_whatsapp(telefone, "🤖 *Atendimento Automático Reativado*.", empresa.evolution_instance)
                    logger.info(f"[{telefone}] Robô reativado pelo corretor via chat (/reativar).")
                    return {"status": "ok", "mensagem": "reativado_via_chat"}
                return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_bot"}
                
            # Tratar Áudio
            elif message_type == "audioMessage" or "audioMessage" in msg_obj:
                cliente_enviou_audio = True
                base64_audio = msg_obj.get("base64") or event_data.get("base64")
                
                if base64_audio:
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
                    return {"status": "ignorado", "motivo": "audio_sem_base64"}

        if not mensagem:
            return {"status": "ignorado", "motivo": "sem_texto"}

        # 3. Adicionar mensagem ao Buffer (Debounce)
        # O cliente pode ter enviado áudio, e depois texto.
        # Vamos passar o cliente_enviou_audio via callback criando um wrapper (closure) ou partial
        import functools
        callback = functools.partial(processar_pipeline_callback, cliente_enviou_audio=cliente_enviou_audio)
        
        adicionar_mensagem(empresa, telefone, mensagem, callback)
        
        # Retorna IMEDIATAMENTE para a Evolution API
        return {"status": "ok", "mensagem": "adicionada_ao_buffer"}
    finally:
        db.close()

@app.delete("/transbordo/{token}/{telefone}")
def reativar_robo(token: str, telefone: str):
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.webhook_token == token).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        from app.pipeline import atualizar_status_transbordo
        atualizar_status_transbordo(db, empresa.id, telefone, None)
        logger.info(f"[{telefone}] Robô reativado manualmente via API para a empresa {empresa.nome}.")
        return {"status": "ok", "mensagem": f"Robô reativado para {telefone}"}
    finally:
        db.close()