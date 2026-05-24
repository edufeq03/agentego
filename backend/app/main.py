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

from app.agenda_api import router as agenda_router
app.include_router(agenda_router, prefix="/api/dashboard/agenda", tags=["agenda"])

from app.admin_api import router as admin_router
from app.middleware import security_middleware

from fastapi.staticfiles import StaticFiles

app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

# Criar pasta de uploads se não existir
if not os.path.exists("app/uploads"):
    os.makedirs("app/uploads")

# Monta pasta de uploads para acesso via URL
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

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
                loop.run_until_complete(disparar_comunicado_background(com.empresa_id, com.mensagem, com.imagem_url, com.id))
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

            config_data = empresa.configuracoes.config if empresa.configuracoes else {}
            nome_empresa = config_data.get("nome_empresa", empresa.nome)
            nome_agente = config_data.get("nome_agente", "Assistente")
            
            # Dias configurados
            dia_aviso_1 = int(config_data.get("aviso_vencimento_1", 7))
            dia_aviso_2 = int(config_data.get("aviso_vencimento_2", 3))
            dia_aviso_3 = int(config_data.get("aviso_vencimento_3", 0))

            mensagem = None

            if dias == dia_aviso_1 and not membro.aviso_7_dias_enviado:
                mensagem = (
                    f"Olá, *{membro.nome}*! 👋\n\n"
                    f"Aqui é o(a) {nome_agente} da *{nome_empresa}*.\n\n"
                    f"Passando para lembrar que seu plano "
                    f"*{membro.plano_nome or 'atual'}* vence em "
                    f"*{dia_aviso_1} dias* (dia {membro.data_vencimento.strftime('%d/%m/%Y')}).\n\n"
                    f"Para renovar ou tirar dúvidas, é só falar aqui! 😊"
                )
                membro.aviso_7_dias_enviado = True

            elif dias == dia_aviso_2 and not membro.aviso_3_dias_enviado:
                mensagem = (
                    f"Olá, *{membro.nome}*! ⚠️\n\n"
                    f"Seu plano *{membro.plano_nome or 'atual'}* na "
                    f"*{nome_empresa}* vence em *{dia_aviso_2} dias* "
                    f"(dia {membro.data_vencimento.strftime('%d/%m/%Y')}).\n\n"
                    f"Não deixe sua matrícula vencer! Renove agora e "
                    f"continue treinando. 💪"
                )
                membro.aviso_3_dias_enviado = True

            elif dias <= dia_aviso_3 and not membro.aviso_vencido_enviado:
                # Caso o aviso 3 seja "no dia" (0) ou já tenha vencido
                texto_dias = "hoje" if dia_aviso_3 == 0 else f"em {dia_aviso_3} dias"
                if dias < 0:
                    texto_dias = "recentemente"
                    
                mensagem = (
                    f"Olá, *{membro.nome}*! 😊\n\n"
                    f"Seu plano na *{nome_empresa}* vence {texto_dias} "
                    f"({membro.data_vencimento.strftime('%d/%m/%Y')}).\n\n"
                    f"Sentimos sua falta! Fale com a gente para renovar "
                    f"e voltar a treinar. 🏋️"
                )
                membro.aviso_vencido_enviado = True

            if mensagem:
                try:
                    enviar_whatsapp(membro.telefone, mensagem, empresa.evolution_instance)
                    logger.info(f"Aviso enviado para {membro.nome} ({membro.telefone})")
                    # Delay dinâmico para segurança
                    import asyncio
                    import random
                    await asyncio.sleep(5 + random.uniform(0, 5))
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
                # Delay dinâmico para segurança
                import asyncio
                import random
                await asyncio.sleep(5 + random.uniform(0, 5))
            except Exception as e:
                logger.error(f"Falha ao enviar aviso de obrigação para {empresa.nome}: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Erro na tarefa de obrigações: {e}")
    finally:
        db.close()

async def tarefa_reengajamento_automatico():
    """Tarefa periódica para verificar e disparar reengajamentos inteligentes por IA em cadência (multi-step)."""
    logger.info("Iniciando varredura de reengajamento inteligente por IA...")
    db = SessionLocal()
    try:
        from datetime import datetime
        from app.database import Empresa, Lead, Mensagem, CampoCustomizado
        from app.pipeline import obter_status_transbordo, gerar_mensagem_reengajamento_ia
        from sqlalchemy.orm.attributes import flag_modified
        import asyncio
        import random
        
        # 1. Obter empresas ativas
        empresas = db.query(Empresa).filter(Empresa.ativo == True).all()
        for empresa in empresas:
            config_dict = empresa.configuracoes.config if empresa.configuracoes else {}
            
            inact_enabled = config_dict.get("reengagement_inactivity_enabled", False)
            pend_enabled = config_dict.get("reengagement_pending_enabled", False)
            
            # Se nenhum estiver habilitado, pula a empresa
            if not inact_enabled and not pend_enabled:
                continue
                
            inact_prompt = config_dict.get("reengagement_inactivity_prompt", "")
            pend_prompt = config_dict.get("reengagement_pending_prompt", "")
            
            # Processar passos de inatividade com fallback
            inact_steps = config_dict.get("reengagement_inactivity_steps")
            if not inact_steps:
                old_prompt = config_dict.get("reengagement_inactivity_prompt")
                old_delay = config_dict.get("reengagement_inactivity_delay_hours")
                if old_prompt is not None:
                    inact_steps = [{"step": 1, "delay_hours": float(old_delay or 2), "prompt": old_prompt}]
                else:
                    inact_steps = [{"step": 1, "delay_hours": 2.0, "prompt": inact_prompt or "Pergunte se o cliente ainda tem interesse."}]

            # Processar passos de campos pendentes com fallback
            pend_steps = config_dict.get("reengagement_pending_steps")
            if not pend_steps:
                old_prompt = config_dict.get("reengagement_pending_prompt")
                old_delay = config_dict.get("reengagement_pending_delay_hours")
                if old_prompt is not None:
                    pend_steps = [{"step": 1, "delay_hours": float(old_delay or 1), "prompt": old_prompt}]
                else:
                    pend_steps = [{"step": 1, "delay_hours": 1.0, "prompt": pend_prompt or "Lembre o lead das informações pendentes ({campos_pendentes})."}]
            
            # 2. Obter leads da empresa em estágio de 'novo' ou 'triagem'
            leads = db.query(Lead).filter(
                Lead.empresa_id == empresa.id,
                Lead.stage.in_(["novo", "triagem"])
            ).all()
            
            for lead in leads:
                # 3. Guardrail: Se o transbordo estiver pausado (atendimento humano), nunca reengajar!
                status_transbordo = obter_status_transbordo(db, empresa.id, lead.telefone)
                if status_transbordo == "pausado":
                    continue
                    
                # 4. Obter a última mensagem da conversa
                ultimo_msg = db.query(Mensagem).filter(
                    Mensagem.lead_id == lead.id
                ).order_by(Mensagem.timestamp.desc()).first()
                
                if not ultimo_msg:
                    continue
                    
                # Apenas reengaja se a última mensagem foi do robô ou do próprio reengajamento (tipo "agente")
                if ultimo_msg.tipo != "agente":
                    continue
                    
                # Garantir dicionário dados_customizados inicializado
                dados_custom = lead.dados_customizados or {}
                if not isinstance(dados_custom, dict):
                    dados_custom = {}
                
                # Rastrear chaves de cadência
                fluxo_ativo = dados_custom.get("reengajamento_fluxo_ativo")
                passo_atual = dados_custom.get("reengajamento_passo_atual", 0) or 0
                ultimo_reeng_ts_str = dados_custom.get("reengajamento_ultimo_timestamp")
                
                # Calcular tempos decorridos
                now = datetime.utcnow()
                elapsed_since_last_msg = (now - ultimo_msg.timestamp).total_seconds() / 3600.0
                
                # Se não houver uma cadência ativa para esse bloco de silêncio, começamos o Passo 1
                if not fluxo_ativo:
                    se_disparou = False
                    
                    # A. Gatilho de Triagem Incompleta (Campos Pendentes) - Prioridade
                    if pend_enabled and len(pend_steps) > 0:
                        # Encontrar campos requeridos pendentes
                        campos_definidos = db.query(CampoCustomizado).filter(
                            CampoCustomizado.empresa_id == empresa.id,
                            CampoCustomizado.ativo == True,
                            CampoCustomizado.obrigatorio == True
                        ).all()
                        
                        campos_pendentes = []
                        for campo in campos_definidos:
                            val = dados_custom.get(campo.chave)
                            if val is None or val == "":
                                campos_pendentes.append(campo.label)
                                
                        if len(campos_pendentes) > 0:
                            step1 = pend_steps[0]
                            if elapsed_since_last_msg >= step1["delay_hours"]:
                                # Disparar Passo 1 dos pendentes!
                                campos_pendentes_str = ", ".join(campos_pendentes)
                                prompt_final = step1["prompt"].replace("{campos_pendentes}", campos_pendentes_str)
                                
                                gerar_mensagem_reengajamento_ia(
                                    db, empresa, lead, prompt_final, campos_pendentes_str=campos_pendentes_str
                                )
                                
                                dados_custom["reengajamento_fluxo_ativo"] = "pending"
                                dados_custom["reengajamento_passo_atual"] = 1
                                dados_custom["reengajamento_ultimo_timestamp"] = now.isoformat()
                                lead.dados_customizados = dados_custom
                                flag_modified(lead, "dados_customizados")
                                db.commit()
                                se_disparou = True
                                
                                await asyncio.sleep(4 + random.uniform(0, 3))
                                
                    # B. Gatilho de Inatividade
                    if inact_enabled and len(inact_steps) > 0 and not se_disparou:
                        step1 = inact_steps[0]
                        if elapsed_since_last_msg >= step1["delay_hours"]:
                            # Disparar Passo 1 da inatividade!
                            gerar_mensagem_reengajamento_ia(db, empresa, lead, step1["prompt"])
                            
                            dados_custom["reengajamento_fluxo_ativo"] = "inactivity"
                            dados_custom["reengajamento_passo_atual"] = 1
                            dados_custom["reengajamento_ultimo_timestamp"] = now.isoformat()
                            lead.dados_customizados = dados_custom
                            flag_modified(lead, "dados_customizados")
                            db.commit()
                            
                            await asyncio.sleep(4 + random.uniform(0, 3))
                            
                else:
                    # Cadência já ativa! Verificamos se é hora de enviar o próximo passo.
                    if not ultimo_reeng_ts_str:
                        continue
                        
                    steps = pend_steps if fluxo_ativo == "pending" else inact_steps
                    enabled = pend_enabled if fluxo_ativo == "pending" else inact_enabled
                    
                    if not enabled:
                        continue
                        
                    # O próximo passo na lista é o index = passo_atual (porque passo_atual = 1-based, ex: após enviar passo 1, o próximo passo é o index 1, i.e., o 2º item da lista)
                    next_step_idx = passo_atual
                    if next_step_idx < len(steps):
                        next_step = steps[next_step_idx]
                        ultimo_reeng_dt = datetime.fromisoformat(ultimo_reeng_ts_str)
                        elapsed_since_last_reeng = (now - ultimo_reeng_dt).total_seconds() / 3600.0
                        
                        if elapsed_since_last_reeng >= next_step["delay_hours"]:
                            # Disparar próximo passo!
                            if fluxo_ativo == "pending":
                                # Verificar se ainda restam campos pendentes
                                campos_definidos = db.query(CampoCustomizado).filter(
                                    CampoCustomizado.empresa_id == empresa.id,
                                    CampoCustomizado.ativo == True,
                                    CampoCustomizado.obrigatorio == True
                                ).all()
                                
                                campos_pendentes = []
                                for campo in campos_definidos:
                                    val = dados_custom.get(campo.chave)
                                    if val is None or val == "":
                                        campos_pendentes.append(campo.label)
                                        
                                if len(campos_pendentes) == 0:
                                    # Triagem concluída no meio tempo, encerra a cadência!
                                    dados_custom.pop("reengajamento_fluxo_ativo", None)
                                    dados_custom.pop("reengajamento_passo_atual", None)
                                    dados_custom.pop("reengajamento_ultimo_timestamp", None)
                                    lead.dados_customizados = dados_custom
                                    flag_modified(lead, "dados_customizados")
                                    db.commit()
                                    continue
                                    
                                campos_pendentes_str = ", ".join(campos_pendentes)
                                prompt_final = next_step["prompt"].replace("{campos_pendentes}", campos_pendentes_str)
                                
                                gerar_mensagem_reengajamento_ia(
                                    db, empresa, lead, prompt_final, campos_pendentes_str=campos_pendentes_str
                                )
                            else:
                                # Inatividade
                                gerar_mensagem_reengajamento_ia(db, empresa, lead, next_step["prompt"])
                                
                            # Atualizar estado para a próxima etapa
                            dados_custom["reengajamento_passo_atual"] = next_step["step"]
                            dados_custom["reengajamento_ultimo_timestamp"] = now.isoformat()
                            lead.dados_customizados = dados_custom
                            flag_modified(lead, "dados_customizados")
                            db.commit()
                            
                            await asyncio.sleep(4 + random.uniform(0, 3))
                            
    except Exception as e:
        logger.error(f"Erro na execução da tarefa de reengajamento automático: {e}", exc_info=True)
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
    scheduler.add_job(tarefa_reengajamento_automatico, 'interval', minutes=5, id="tarefa_reengajamento_automatico")
    
    from app.agenda_service import tarefa_processar_agenda
    scheduler.add_job(tarefa_processar_agenda, 'interval', minutes=5, id="tarefa_processar_agenda")
    
    scheduler.start()
    logger.info("Scheduler iniciado: Relatórios semanais, Manutenção, Reengajamento e Agenda.")


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
        
        config_dict = empresa.configuracoes.config if empresa.configuracoes else {}
        modulos = config_dict.get("modulos_ativos", [])
        
        if "agenda" in modulos or empresa.nicho == "agenda":
            from app.pipeline_agenda import processar_pipeline_agenda
            resultado = processar_pipeline_agenda(empresa, telefone, texto_combinado)
        elif empresa.nicho == "lanchonete":
            from app.pipeline_lanchonete import processar_pipeline_lanchonete
            resultado = processar_pipeline_lanchonete(empresa, telefone, texto_combinado)
        else:
            resultado = processar_webhook(empresa, telefone, texto_combinado)
        logger.info(f"✅ [IA] Resposta pronta para {telefone}")
        
        if resultado["status"] == "pausado":
            logger.info(f"[{telefone}] Número pausado (transbordo ativo). Mensagem ignorada.")
            return

        if resultado["status"] == "ignorado":
            logger.info(f"🚫 [{telefone}] MENSAGEM BLOQUEADA (Blacklist). Nenhuma resposta será enviada.")
            return

        resposta = resultado["resposta"]
        logger.info(f"[{telefone}] Cliente: '{texto_combinado}' -> IA: '{resposta}'")

        # Enviar Resposta via Evolution API
        config = empresa.configuracoes.config if empresa.configuracoes else {}
        tts_enabled = config.get("tts_enabled", True)
        tts_always = config.get("tts_always", False)
        tts_voice = config.get("tts_voice", "nova")
        provedor_tts = config.get("provedor_tts", "openai")
        elevenlabs_voice_id = config.get("elevenlabs_voice_id")
        
        # Obter e decriptografar a chave API do ElevenLabs
        from app.utils_crypto import decrypt_key
        elevenlabs_api_key = decrypt_key(config.get("elevenlabs_api_key", ""))

        if tts_enabled and (cliente_enviou_audio or tts_always):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_out:
                caminho_audio_resposta = temp_out.name
            try:
                gerar_audio(
                    resposta, 
                    caminho_audio_resposta, 
                    provider=provedor_tts, 
                    voice=tts_voice,
                    api_key=elevenlabs_api_key,
                    voice_id=elevenlabs_voice_id
                )
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
            
            # Sincronização automática do nome de perfil (pushName) do WhatsApp
            push_name = data.get("pushName") or data.get("senderName")
            if "data" in data and isinstance(data["data"], dict):
                push_name = push_name or data["data"].get("pushName") or data["data"].get("senderName")
            
            if push_name and isinstance(push_name, str):
                push_name = push_name.strip()
                
            if telefone and push_name:
                try:
                    from app.database import Lead
                    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
                    if not lead:
                        lead = Lead(empresa_id=empresa.id, telefone=telefone, nome=push_name, stage="novo")
                        db.add(lead)
                        db.commit()
                    elif not lead.nome or lead.nome == lead.telefone:
                        lead.nome = push_name
                        db.commit()
                    logger.info(f"👤 [CONTACT SYNC] Nome do WhatsApp sincronizado para {telefone}: {push_name}")
                except Exception as e:
                    logger.error(f"Erro ao salvar nome de perfil do WhatsApp para {telefone}: {e}")
            
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
                if not config.get("stt_enabled", True):
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

        # 2.5 Tratar Imagens e OCR se for corretora
        if (message_type == "imageMessage" or "imageMessage" in msg_obj) and empresa.nicho == "corretora":
            logger.info(f"[{telefone}] Imagem recebida para corretora! Iniciando OCR...")
            base64_imagem = msg_obj.get("base64") or event_data.get("base64")
            image_msg = msg_obj.get("imageMessage") or msg_obj
            
            # Se não tiver base64, tenta fazer download via downloadMedia
            if not base64_imagem:
                webhook_server_url = data.get("server_url")
                if webhook_server_url:
                    base_url_evolution = webhook_server_url.rstrip('/')
                else:
                    from app.whatsapp_service import get_evolution_base_url
                    base_url_evolution = get_evolution_base_url().rstrip('/')

                webhook_apikey = data.get("apikey")
                headers = {"apikey": webhook_apikey or os.getenv("EVOLUTION_API_KEY"), "Content-Type": "application/json"}
                
                webhook_instance_id = data.get("instanceId") or data.get("data", {}).get("instanceId")
                inst_ref = webhook_instance_id or empresa.evolution_instance
                
                endpoints_tentar = [
                    f"{base_url_evolution}/chat/downloadMedia",
                    f"{base_url_evolution}/v2/chat/downloadMedia",
                    f"{base_url_evolution}/message/getBase64FromMedia/{inst_ref}",
                    f"{base_url_evolution}/v2/message/getBase64FromMedia/{inst_ref}",
                    f"{base_url_evolution}/chat/getBase64FromMedia/{inst_ref}",
                ]
                
                payload_dl = {
                    "instance": empresa.evolution_instance,
                    "mediaKey": image_msg.get("mediaKey"),
                    "directPath": image_msg.get("directPath"),
                    "mimetype": image_msg.get("mimetype", "image/jpeg"),
                    "url": image_msg.get("url"),
                    "type": "image"
                }
                
                for url_dl in endpoints_tentar:
                    try:
                        res_dl = requests.post(url_dl, json=payload_dl, headers=headers, timeout=15)
                        if res_dl.status_code in [200, 201]:
                            base64_imagem = res_dl.json().get("base64")
                            if base64_imagem:
                                logger.info(f"[{telefone}] Imagem descriptografada via Evolution API.")
                                break
                    except Exception:
                        continue

            if base64_imagem:
                if "," in base64_imagem:
                    base64_imagem = base64_imagem.split(",")[1]
                mimetype = image_msg.get("mimetype", "image/jpeg") if "imageMessage" in msg_obj else "image/jpeg"
                
                try:
                    from app.ocr_service import classificar_e_processar_ocr
                    from datetime import datetime
                    from app.database import LeadSeguro
                    ocr_res = classificar_e_processar_ocr(base64_imagem, mimetype)
                    logger.info(f"[{telefone}] OCR processado: {ocr_res}")
                    tipo_doc = ocr_res.get("tipo", "outro")
                    dados_doc = ocr_res.get("dados", {})
                    
                    # Procurar ou criar lead/lead_seguro correspondente
                    lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
                    if not lead:
                        lead = Lead(empresa_id=empresa.id, telefone=telefone, stage="primeiro_contato")
                        db.add(lead)
                        db.commit()
                        db.refresh(lead)
                    
                    lead_seguro = db.query(LeadSeguro).filter(LeadSeguro.id == lead.id).first()
                    if not lead_seguro:
                        lead_seguro = LeadSeguro(
                            id=lead.id,
                            empresa_id=empresa.id,
                            telefone=telefone,
                            canal_entrada="organico",
                            stage=lead.stage
                        )
                        db.add(lead_seguro)
                        db.commit()
                        db.refresh(lead_seguro)
                    
                    # Salvar no BD baseado no tipo
                    if tipo_doc == "cnh":
                        lead_seguro.nome_segurado = dados_doc.get("nome") or lead_seguro.nome_segurado
                        lead.nome = dados_doc.get("nome") or lead.nome
                        if dados_doc.get("cpf") and hasattr(lead, "cpf"):
                            lead.cpf = dados_doc.get("cpf")
                        
                        docs_r = lead_seguro.docs_recebidos or []
                        if "cnh_ou_rg" not in [d.get("tipo") for d in docs_r]:
                            docs_r.append({"tipo": "cnh_ou_rg", "recebido_em": str(datetime.utcnow())})
                            lead_seguro.docs_recebidos = docs_r
                        
                        docs_p = lead_seguro.docs_pendentes or []
                        if "cnh_ou_rg" in docs_p:
                            docs_p.remove("cnh_ou_rg")
                            lead_seguro.docs_pendentes = docs_p
                            
                    elif tipo_doc == "crlv":
                        lead_seguro.placa = dados_doc.get("placa") or lead_seguro.placa
                        lead_seguro.marca_modelo = f"{dados_doc.get('marca', '')} {dados_doc.get('modelo', '')}".strip() or lead_seguro.marca_modelo
                        try:
                            if dados_doc.get("ano_fabricacao"):
                                lead_seguro.ano_fabricacao = int(dados_doc.get("ano_fabricacao"))
                            if dados_doc.get("ano_modelo"):
                                lead_seguro.ano_modelo = int(dados_doc.get("ano_modelo"))
                        except Exception:
                            pass
                            
                        docs_r = lead_seguro.docs_recebidos or []
                        if "crlv" not in [d.get("tipo") for d in docs_r]:
                            docs_r.append({"tipo": "crlv", "recebido_em": str(datetime.utcnow())})
                            lead_seguro.docs_recebidos = docs_r
                        
                        docs_p = lead_seguro.docs_pendentes or []
                        if "crlv" in docs_p:
                            docs_p.remove("crlv")
                            lead_seguro.docs_pendentes = docs_p
                            
                    elif tipo_doc == "carteirinha_plano":
                        lead_seguro.plano_anterior_nome = dados_doc.get("plano_nome") or dados_doc.get("operadora") or lead_seguro.plano_anterior_nome
                        lead_seguro.tem_plano_anterior = True
                        
                        docs_r = lead_seguro.docs_recebidos or []
                        if "carteirinha" not in [d.get("tipo") for d in docs_r]:
                            docs_r.append({"tipo": "carteirinha", "recebido_em": str(datetime.utcnow())})
                            lead_seguro.docs_recebidos = docs_r
                        
                        docs_p = lead_seguro.docs_pendentes or []
                        if "carteirinha" in docs_p:
                            docs_p.remove("carteirinha")
                            lead_seguro.docs_pendentes = docs_p
                    
                    db.commit()
                    
                    # Criar registro DocumentoSeguro
                    from app.database import DocumentoSeguro
                    import uuid
                    doc_db = DocumentoSeguro(
                        id=uuid.uuid4(),
                        lead_id=lead.id,
                        empresa_id=empresa.id,
                        tipo=tipo_doc,
                        arquivo_url=image_msg.get("url", ""),
                        mimetype=mimetype,
                        ocr_processado=True,
                        ocr_resultado=dados_doc,
                        ocr_confianca=ocr_res.get("confianca", 1.0)
                    )
                    db.add(doc_db)
                    db.commit()
                    
                    mensagem = f"[DOCUMENTO_RECEBIDO: tipo={tipo_doc}]"
                except Exception as ocr_ex:
                    logger.error(f"Erro ao processar OCR da imagem: {ocr_ex}")

        if not mensagem:
            logger.info(f"[{telefone}] Webhook ignorado: Mensagem sem texto ou tipo não suportado.")
            return {"status": "ignorado", "motivo": "sem_texto"}

        # Verificar se a mensagem é do WhatsApp da Cozinha
        config = empresa.configuracoes.config if empresa.configuracoes else {}
        tel_cozinha = config.get("whatsapp_cozinha")
        if tel_cozinha:
            tel_cozinha_norm = "".join(filter(str.isdigit, str(tel_cozinha)))
            telefone_norm = "".join(filter(str.isdigit, str(telefone)))
            # Comparacao segura usando os ultimos 9 digitos para evitar falsos positivos
            if len(tel_cozinha_norm) >= 8 and len(telefone_norm) >= 8 and tel_cozinha_norm[-9:] == telefone_norm[-9:]:
                logger.info(f"🍳 [COZINHA] Processando comando síncrono para {telefone}...")
                from app.pipeline_cozinha import processar_comando_cozinha
                res_cozinha = processar_comando_cozinha(empresa, mensagem)
                enviar_whatsapp(telefone, res_cozinha["resposta"], empresa.evolution_instance)
                return {"status": "ok", "mensagem": "cozinha_processada"}

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
