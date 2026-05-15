from dotenv import load_dotenv
load_dotenv()

import logging
import requests
from fastapi import FastAPI, Request, HTTPException, Depends
from datetime import timedelta
from sqlalchemy.orm import Session
import asyncio

from app.logger import setup_logging
logger = setup_logging()

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

def tarefa_disparo_agendado():
    """Verifica e dispara comunicados agendados."""
    from app.database import SessionLocal, Comunicado, Empresa
    from app.dashboard_api import disparar_comunicado_background
    from datetime import datetime
    import asyncio
    
    db = SessionLocal()
    try:
        agora = datetime.now()
        pendentes = db.query(Comunicado).filter(
            Comunicado.status == 'pendente',
            Comunicado.data_programada <= agora
        ).all()
        
        for com in pendentes:
            logger.info(f"Disparando comunicado agendado {com.id} para empresa {com.empresa_id}")
            com.status = "enviando"
            db.commit()
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(disparar_comunicado_background(com.empresa_id, com.mensagem))
                com.status = "enviado"
                com.enviado_em = datetime.now()
            except Exception as e:
                logger.error(f"Erro no disparo agendado {com.id}: {e}")
                com.status = "erro"
            finally:
                db.commit()
    finally:
        db.close()

async def tarefa_avisos_vencimento():
    """Roda diariamente às 09:00 e envia avisos de vencimento de plano."""
    logger.info("Iniciando tarefa de avisos de vencimento...")
    db = SessionLocal()
    try:
        from app.database import MembroAcademia
        from app.whatsapp import enviar_whatsapp
        from datetime import datetime
        agora = datetime.utcnow()

        # Buscar membros ativos
        membros_alertar = db.query(MembroAcademia).filter(
            MembroAcademia.ativo == True
        ).all()

        for membro in membros_alertar:
            dias = (membro.data_vencimento - agora).days
            empresa = db.query(Empresa).filter(
                Empresa.id == membro.empresa_id,
                Empresa.ativo == True
            ).first()
            if not empresa:
                continue

            config = empresa.configuracoes.config if empresa.configuracoes else {}
            nome_empresa = config.get("nome_empresa", empresa.nome)
            nome_agente = config.get("nome_agente", "Assistente")

            mensagem = None

            if dias == 7 and not membro.aviso_7_dias_enviado:
                mensagem = (
                    f"Olá, *{membro.nome}*! 👋\n\n"
                    f"Aqui é o(a) {nome_agente} da *{nome_empresa}*.\n\n"
                    f"Passando para lembrar que seu plano "
                    f"*{membro.plano_nome or 'atual'}* vence em "
                    f"*7 dias* (dia {membro.data_vencimento.strftime('%d/%m/%Y')}).\n\n"
                    f"Para renovar ou tirar dúvidas, é só falar aqui! 😊"
                )
                membro.aviso_7_dias_enviado = True

            elif dias == 3 and not membro.aviso_3_dias_enviado:
                mensagem = (
                    f"Olá, *{membro.nome}*! ⚠️\n\n"
                    f"Seu plano *{membro.plano_nome or 'atual'}* na "
                    f"*{nome_empresa}* vence em *3 dias* "
                    f"(dia {membro.data_vencimento.strftime('%d/%m/%Y')}).\n\n"
                    f"Não deixe sua matrícula vencer! Renove agora e "
                    f"continue treinando. 💪"
                )
                membro.aviso_3_dias_enviado = True

            elif dias < 0 and not membro.aviso_vencido_enviado:
                mensagem = (
                    f"Olá, *{membro.nome}*! 😊\n\n"
                    f"Seu plano na *{nome_empresa}* venceu em "
                    f"{membro.data_vencimento.strftime('%d/%m/%Y')}.\n\n"
                    f"Sentimos sua falta! Fale com a gente para renovar "
                    f"e voltar a treinar. 🏋️"
                )
                membro.aviso_vencido_enviado = True

            if mensagem:
                try:
                    enviar_whatsapp(membro.telefone, mensagem, empresa.evolution_instance)
                    logger.info(f"Aviso enviado para {membro.nome} ({membro.telefone})")
                except Exception as e:
                    logger.error(f"Falha ao enviar aviso para {membro.telefone}: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Erro na tarefa de avisos: {e}")
    finally:
        db.close()

async def tarefa_avisos_obrigacoes():
    """Avisa o proprietário do escritório sobre obrigações nos próximos 3 dias."""
    logger.info("Iniciando tarefa de avisos de obrigações fiscais...")
    db = SessionLocal()
    try:
        from app.database import ObrigacaoFiscal
        from app.whatsapp import enviar_whatsapp
        from datetime import datetime, timedelta
        agora = datetime.utcnow()
        em_3_dias = agora + timedelta(days=3)

        obrigacoes = db.query(ObrigacaoFiscal).filter(
            ObrigacaoFiscal.prazo <= em_3_dias,
            ObrigacaoFiscal.prazo >= agora,
            ObrigacaoFiscal.status == "pendente",
            ObrigacaoFiscal.aviso_enviado == False
        ).all()

        for ob in obrigacoes:
            empresa = db.query(Empresa).filter(
                Empresa.id == ob.empresa_id,
                Empresa.ativo == True,
                Empresa.telefone_proprietario.isnot(None)
            ).first()
            if not empresa:
                continue

            dias = (ob.prazo - agora).days
            msg = (
                f"⚠️ *Lembrete de Obrigação Fiscal*\n\n"
                f"*{ob.titulo}*\n"
                f"Prazo: *{ob.prazo.strftime('%d/%m/%Y')}* "
                f"({'hoje' if dias == 0 else f'em {dias} dia(s)'})\n\n"
                f"{ob.descricao or ''}"
            )
            try:
                enviar_whatsapp(empresa.telefone_proprietario, msg, empresa.evolution_instance)
                ob.aviso_enviado = True
                logger.info(f"Aviso de obrigação enviado para {empresa.nome}")
            except Exception as e:
                logger.error(f"Falha ao enviar aviso de obrigação para {empresa.nome}: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Erro na tarefa de obrigações: {e}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    # Agenda para toda Segunda-feira às 09:00 AM
    scheduler.add_job(tarefa_relatorio_semanal, 'cron', day_of_week='mon', hour=9, minute=0)
    # Agenda manutenção diária à meia-noite
    scheduler.add_job(tarefa_manutencao_diaria, 'cron', hour=0, minute=0)
    # Agenda avisos de academia às 09:00
    scheduler.add_job(tarefa_avisos_vencimento, 'cron', hour=9, minute=0, id="tarefa_avisos_vencimento")
    scheduler.add_job(tarefa_avisos_obrigacoes, 'cron', hour=8, minute=0, id="tarefa_avisos_obrigacoes")
    scheduler.add_job(tarefa_disparo_agendado, 'interval', minutes=10, id="tarefa_disparo_agendado")
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
        tts_voice = config.get("tts_voice", "nova")

        if tts_enabled and (cliente_enviou_audio or tts_always):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_out:
                caminho_audio_resposta = temp_out.name
            try:
                gerar_audio(resposta, caminho_audio_resposta, voice=tts_voice)
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
@limiter.limit("60/minute")
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
                
                # FALLBACK: Se ainda não tiver base64, tenta vários endpoints da Evolution
                if not base64_audio and "audioMessage" in msg_obj:
                    audio_msg = msg_obj["audioMessage"]
                    from app.whatsapp_service import get_evolution_base_url
                    base_url_evolution = get_evolution_base_url()
                    
                    # Lista de endpoints para tentar (em ordem de probabilidade)
                    webhook_server_url = data.get("server_url")
                    if webhook_server_url:
                        logger.info(f"DEBUG EVOLUTION - Usando server_url do Webhook: {webhook_server_url}")
                        base_url_evolution = webhook_server_url.rstrip('/')
                    else:
                        from app.whatsapp_service import get_evolution_base_url
                        base_url_evolution = get_evolution_base_url().rstrip('/')

                    webhook_apikey = data.get("apikey")
                    headers = {"apikey": webhook_apikey or os.getenv("EVOLUTION_API_KEY"), "Content-Type": "application/json"}
                    
                    webhook_instance_id = data.get("instanceId") or data.get("data", {}).get("instanceId")
                    inst_ref = webhook_instance_id or empresa.evolution_instance
                    
                    # Lista de endpoints para tentar (em ordem de probabilidade, com e sem prefixo /v2)
                    endpoints_tentar = [
                        f"{base_url_evolution}/chat/downloadMedia",
                        f"{base_url_evolution}/v2/chat/downloadMedia",
                        f"{base_url_evolution}/message/getBase64FromMedia/{inst_ref}",
                        f"{base_url_evolution}/v2/message/getBase64FromMedia/{inst_ref}",
                        f"{base_url_evolution}/chat/getBase64FromMedia/{inst_ref}",
                    ]
                    
                    # Log de versão e teste de conectividade para debug
                    try:
                        res_v = requests.get(f"{base_url_evolution}/v2/version", headers=headers, timeout=5)
                        logger.info(f"DEBUG EVOLUTION - Versão /v2: {res_v.status_code}")
                        res_fi = requests.get(f"{base_url_evolution}/instance/fetchInstances", headers=headers, timeout=5)
                        logger.info(f"DEBUG EVOLUTION - Teste fetchInstances: {res_fi.status_code}")
                    except: pass
                    
                    payload_dl = {
                        "instance": empresa.evolution_instance,
                        "mediaKey": audio_msg.get("mediaKey"),
                        "directPath": audio_msg.get("directPath"),
                        "mimetype": audio_msg.get("mimetype"),
                        "url": audio_msg.get("url"),
                        "type": "audio"
                    }
                    headers = {"apikey": os.getenv("EVOLUTION_API_KEY"), "Content-Type": "application/json"}
                    
                    for url_dl in endpoints_tentar:
                        try:
                            res_dl = requests.post(url_dl, json=payload_dl, headers=headers, timeout=15)
                            if res_dl.status_code in [200, 201]:
                                base64_audio = res_dl.json().get("base64")
                                if base64_audio:
                                    logger.info(f"[{telefone}] Áudio descriptografado via Evolution API.")
                                    break
                        except Exception:
                            continue
                
                # Se agora temos o base64
                if base64_audio:
                    if "," in base64_audio:
                        base64_audio = base64_audio.split(",")[1]
                    audio_content = base64.b64decode(base64_audio)
                else:
                    audio_content = None

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
                    audio_content = None

                if not audio_content:
                    logger.info(f"[{telefone}] Webhook ignorado: Áudio recebido mas sem conteúdo legível.")
                    return {"status": "ignorado", "motivo": "audio_sem_conteudo"}

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
