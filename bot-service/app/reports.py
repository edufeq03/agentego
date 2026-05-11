from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import Lead, Mensagem, Evento, Empresa
import logging

logger = logging.getLogger(__name__)

def gerar_dados_semanais(db: Session, empresa_id: str):
    """
    Consolida as métricas da última semana (7 dias).
    """
    hoje = datetime.utcnow()
    sete_dias_atras = hoje - timedelta(days=7)
    
    # 1. Total de conversas (leads) ativos na semana
    # Consideramos leads que enviaram mensagem nos últimos 7 dias
    leads_ativos = db.query(func.count(func.distinct(Mensagem.lead_id)))\
        .filter(Mensagem.empresa_id == empresa_id, Mensagem.timestamp >= sete_dias_atras)\
        .scalar() or 0
        
    # 2. Novos leads captados
    novos_leads = db.query(func.count(Lead.id))\
        .filter(Lead.empresa_id == empresa_id, Lead.criado_em >= sete_dias_atras)\
        .scalar() or 0
        
    # 3. Conversões (Eventos relacionados a visita)
    visitas = db.query(func.count(Evento.id))\
        .filter(Evento.empresa_id == empresa_id, Evento.tipo.in_(["visita_aceita", "perguntou_visita"]), Evento.timestamp >= sete_dias_atras)\
        .scalar() or 0
        
    # 4. Intenção mais frequente
    top_intencao = db.query(Mensagem.intencao, func.count(Mensagem.id))\
        .filter(Mensagem.empresa_id == empresa_id, Mensagem.tipo == "usuario", Mensagem.timestamp >= sete_dias_atras, Mensagem.intencao.isnot(None))\
        .group_by(Mensagem.intencao)\
        .order_by(func.count(Mensagem.id).desc())\
        .first()
    
    intencao_str = top_intencao[0] if top_intencao else "N/A"
    
    return {
        "leads_ativos": leads_ativos,
        "novos_leads": novos_leads,
        "visitas": visitas,
        "top_intencao": intencao_str
    }

def formatar_relatorio_whatsapp(empresa_nome: str, slug: str, dados: dict):
    """
    Cria a string formatada com emojis para o WhatsApp.
    """
    import os
    base_url = os.getenv("BASE_URL", "https://app.atendia.com.br")
    dashboard_url = f"{base_url}/{slug}"

    msg = (
        f"📊 *Relatório Semanal: {empresa_nome}*\n"
        f"Período: Últimos 7 dias\n\n"
        f"🚀 *Performance Geral:*\n"
        f"• Contatos Ativos: {dados['leads_ativos']}\n"
        f"• Novos Leads: {dados['novos_leads']}\n"
        f"• Visitas Agendadas: {dados['visitas']} ✅\n\n"
        f"💡 *Insights da IA:*\n"
        f"O assunto mais procurado foi: *{dados['top_intencao'].capitalize()}*.\n\n"
        f"📲 *Acesse seu Dashboard:* {dashboard_url}\n\n"
        f"Continue investindo no atendimento rápido para converter esses leads! 🦾"
    )
    return msg

async def enviar_relatorio_semanal_empresa(db: Session, empresa: Empresa):
    """
    Orquestra o cálculo e envio para uma empresa específica.
    """
    from app.whatsapp import enviar_whatsapp
    
    if not empresa.telefone_proprietario:
        logger.warning(f"Empresa {empresa.nome} não possui telefone_proprietario configurado.")
        return False
        
    try:
        dados = gerar_dados_semanais(db, empresa.id)
        mensagem = formatar_relatorio_whatsapp(empresa.nome, empresa.slug, dados)
        
        enviar_whatsapp(empresa.telefone_proprietario, mensagem, empresa.evolution_instance)
        logger.info(f"Relatório semanal enviado para {empresa.nome} ({empresa.telefone_proprietario}) usando instância {empresa.evolution_instance}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar relatório para {empresa.nome}: {e}")
        return False
