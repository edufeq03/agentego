from dotenv import load_dotenv
load_dotenv()

import logging
import requests
from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import asyncio

from app.logger import setup_logging
logger = setup_logging()

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
    allow_origins=[
        "http://localhost:3000",
        "https://agentego.ignotec.com.br",
        "https://agentego.com.br",
        "https://www.agentego.com.br",
        "http://agentego.com.br",
        "http://www.agentego.com.br",
        "https://sites-academia-dashboard.zdgx3l.easypanel.host",
        "https://sites-academia-agente.zdgx3l.easypanel.host",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from app.dashboard_api import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

from app.admin_api import router as admin_router
from app.middleware import security_middleware

app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.middleware("http")
async def security_check(request: Request, call_next):
    return await security_middleware(request, call_next)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}ms".format(process_time)
    
    # Ignora logs de polling frequente e webhooks para não poluir o console
    if response.status_code == 200:
        path = request.url.path
        if path.startswith("/webhook") or \
           path.startswith("/api/dashboard/whatsapp/status") or \
           path.startswith("/api/dashboard/conversas"):
            return response

    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "tipo": "request",
            "method": request.method,
            "path": request.url.path,
            "process_time": formatted_process_time,
            "status_code": response.status_code
        }
    )
    
    return response
    
@app.get("/")
async def root():
    return {
        "app": "AgenteGo API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Testa conexão com banco
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
        
    return {
        "status": "ok",
        "database": db_status,
        "openai": "available" if os.getenv("OPENAI_API_KEY") else "missing"
    }

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

async def tarefa_manutencao_diaria():
    """Roda diariamente para expirar trials e limpezas."""
    logger.info("Iniciando manutenção diária (expiração de trials)...")
    db = SessionLocal()
    try:
        from datetime import datetime
        agora = datetime.utcnow()
        # Expirar trials vencidos
        empresas_trial = db.query(Empresa).filter(
            Empresa.plano == "trial",
            Empresa.data_expiracao_teste < agora,
            Empresa.ativo == True
        ).all()
        for e in empresas_trial:
            e.ativo = False
            logger.info(f"Trial expirado para empresa: {e.nome} (ID: {e.id})")
        db.commit()
    except Exception as e:
        logger.error(f"Erro na manutenção diária: {e}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    # Agenda para toda Segunda-feira às 09:00 AM
    scheduler.add_job(tarefa_relatorio_semanal, 'cron', day_of_week='mon', hour=9, minute=0)
    # Agenda manutenção diária à meia-noite
    scheduler.add_job(tarefa_manutencao_diaria, 'cron', hour=0, minute=0)
    scheduler.start()
    logger.info("Scheduler iniciado: Relatórios semanais (Seg 09h) e Manutenção (00h).")

@app.on_event("shutdown")
def on_shutdown():
    logger.warning("⚠️ EVENTO DE SHUTDOWN RECEBIDO! O container está sendo encerrado.")



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
        logger.info(f"🤖 [IA] Gerando resposta para {telefone}...")
        resultado = processar_webhook(empresa, telefone, texto_combinado)
        logger.info(f"✅ [IA] Resposta pronta para {telefone}")
        
        if resultado["status"] == "pausado":
            logger.info(f"[{telefone}] Número pausado (transbordo ativo). Mensagem ignorada.")
            return

        resposta = resultado["resposta"]
        logger.info(f"[{telefone}] Cliente: '{texto_combinado}' -> IA: '{resposta}'")

        # Enviar Resposta via Evolution API
        config = empresa.configuracoes.config if empresa.configuracoes else {}
        tts_enabled = config.get("tts_enabled", False)
        tts_always = config.get("tts_always", False)

        if tts_enabled and (cliente_enviou_audio or tts_always):
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
        data = await request.json()
        # 2.5: Truncar logs de RAW DATA para evitar poluição com base64
        import json
        if logger.isEnabledFor(logging.DEBUG):
            safe_data = {k: (v[:50] + "...[truncado]" if isinstance(v, str) and len(v) > 50 else v)
                         for k, v in data.items()}
            logger.debug(f"RAW DATA (truncado): {json.dumps(safe_data)}")

        # 1. Identificar Empresa pelo token
        empresa = db.query(Empresa).filter(Empresa.webhook_token == token, Empresa.ativo == True).first()
        if not empresa:
            logger.warning(f"Webhook recebido com token INVÁLIDO ou empresa inativa: {token}")
            return {"status": "erro", "motivo": "token_invalido"}

        # 2. Extrair dados da Evolution API
        event_type = data.get("event", "unknown")
        logger.info(f"🌐 [WEBHOOK] Evento recebido: {event_type}")
        
        # Se não for uma mensagem nova, ignoramos a maioria dos eventos para limpar o log
        if event_type not in ["messages.upsert", "messages.update", "unknown"]:
            return {"status": "ignorado", "motivo": f"evento_{event_type}_nao_processado"}

        mensagem = data.get("message")
        telefone = data.get("phone")
        cliente_enviou_audio = False

        # Extração Robusta (v1 e v2)
        if not mensagem and "data" in data:
            event_data = data["data"]
            msg_obj = event_data.get("message", {})
            message_type = event_data.get("messageType", "conversation")
            
            # 1. Identificar Telefone
            remote_jid = event_data.get("key", {}).get("remoteJid", "")
            if "@s.whatsapp.net" in remote_jid:
                telefone = remote_jid.split("@")[0]
            
            # 2. Evitar Auto-Resposta (Loop)
            if event_data.get("key", {}).get("fromMe") == True:
                # Verificação de comando de reativação via chat
                if "conversation" in msg_obj:
                    texto = msg_obj["conversation"]
                    if texto and texto.strip().lower() == "/reativar":
                        from app.pipeline import atualizar_status_transbordo
                        atualizar_status_transbordo(db, empresa.id, telefone, None)
                        enviar_whatsapp(telefone, "🤖 *Atendimento Automático Reativado*.", empresa.evolution_instance)
                        logger.info(f"[{telefone}] Robô reativado pelo corretor via chat.")
                        return {"status": "ok"}
                return {"status": "ignorado", "motivo": "from_me"}

            # 3. Extrair Texto
            if "conversation" in msg_obj:
                mensagem = msg_obj["conversation"]
            elif "extendedTextMessage" in msg_obj:
                mensagem = msg_obj["extendedTextMessage"].get("text")
            
            # 4. Tratar Áudio
            if message_type == "audioMessage" or "audioMessage" in msg_obj:
                config = empresa.configuracoes.config if empresa.configuracoes else {}
                if not config.get("stt_enabled", False):
                    logger.warning(f"[{telefone}] Áudio recebido, mas STT está DESATIVADO nas configurações.")
                    return {"status": "ignorado", "motivo": "stt_desativado"}

                cliente_enviou_audio = True
                base64_audio = msg_obj.get("base64") or event_data.get("base64")
                
                # Tenta buscar dentro de audioMessage se não estiver no nível superior
                if not base64_audio and "audioMessage" in msg_obj:
                    base64_audio = msg_obj["audioMessage"].get("base64")
                
                # FALLBACK: Se ainda não tiver base64, tenta baixar via URL
                if not base64_audio and "audioMessage" in msg_obj and "url" in msg_obj["audioMessage"]:
                    url_audio = msg_obj["audioMessage"]["url"]
                    logger.info(f"[{telefone}] Base64 ausente, tentando baixar áudio via URL: {url_audio}")
                    try:
                        headers = {"apikey": os.getenv("EVOLUTION_API_KEY")}
                        res_audio = requests.get(url_audio, headers=headers, timeout=10)
                        if res_audio.status_code == 200:
                            audio_content = res_audio.content
                            logger.info(f"[{telefone}] Áudio baixado com sucesso ({len(audio_content)} bytes)")
                        else:
                            logger.error(f"[{telefone}] Falha ao baixar áudio (Status {res_audio.status_code})")
                            audio_content = None
                    except Exception as e:
                        logger.error(f"[{telefone}] Erro ao baixar áudio da URL: {e}")
                        audio_content = None
                else:
                    if base64_audio and "," in base64_audio:
                        base64_audio = base64_audio.split(",")[1]
                    audio_content = base64.b64decode(base64_audio) if base64_audio else None

                if audio_content:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
                        temp_audio.write(audio_content)
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
                    logger.info(f"[{telefone}] Áudio recebido, mas 'base64' ausente.")
                    logger.info(f"DEBUG ESTRUTURA - Chaves do Webhook: {list(data.keys())}")
                    if 'data' in data: logger.info(f"DEBUG ESTRUTURA - Chaves de data['data']: {list(data['data'].keys())}")
                    logger.info(f"DEBUG ESTRUTURA - Chaves de msg_obj: {list(msg_obj.keys())}")
                    if 'audioMessage' in msg_obj: logger.info(f"DEBUG ESTRUTURA - Chaves de audioMessage: {list(msg_obj['audioMessage'].keys())}")
                    
                    return {"status": "ignorado", "motivo": "audio_sem_base64"}

        if not mensagem:
            logger.info(f"[{telefone}] Webhook ignorado: Mensagem sem texto ou tipo não suportado.")
            return {"status": "ignorado", "motivo": "sem_texto"}

        # 3. Adicionar mensagem ao Buffer (Debounce)
        # O cliente pode ter enviado áudio, e depois texto.
        # Vamos passar o cliente_enviou_audio via callback criando um wrapper (closure) ou partial
        import functools
        callback = functools.partial(processar_pipeline_callback, cliente_enviou_audio=cliente_enviou_audio)
        
        logger.info(f"📩 [MENSAGEM RECEBIDA] {telefone} ({empresa.nome}): {mensagem[:50]}...")
        adicionar_mensagem(empresa, telefone, mensagem, callback)
        
        # Retorna IMEDIATAMENTE para a Evolution API
        return {"status": "ok", "mensagem": "adicionada_ao_buffer"}
    finally:
        db.close()
