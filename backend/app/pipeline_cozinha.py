import re
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, Pedido, Cardapio, Empresa, Lead
from app.pedido_service import atualizar_status_pedido, obter_pedido_por_numero, obter_pedidos_ativos
from app.cardapio_service import listar_itens, obter_item_por_nome
from app.whatsapp import enviar_whatsapp

logger = logging.getLogger(__name__)

def processar_comando_cozinha(empresa: Empresa, mensagem_texto: str) -> dict:
    """
    Processador de comandos rápidos da cozinha via WhatsApp.
    Não consome IA (Regex/Heurística) para máxima velocidade e zero custo.
    """
    db = SessionLocal()
    try:
        texto = mensagem_texto.strip().lower()
        logger.info(f"[COZINHA] Comando recebido: '{texto}'")
        
        # 1. Comando: 'pedidos'
        if texto == "pedidos":
            pedidos_ativos = obter_pedidos_ativos(db, empresa.id)
            if not pedidos_ativos:
                return {"status": "ok", "resposta": "🍳 Não há nenhum pedido ativo em andamento no momento."}
                
            resposta_linhas = ["📋 *PEDIDOS ATIVOS EM ANDAMENTO:*"]
            for ped in pedidos_ativos:
                itens_resumo = ", ".join([f"{it.quantidade}x {it.nome}" for it in ped.itens])
                tipo_modo = "Delivery" if ped.modo == "delivery" else ("Mesa #" + str(ped.numero_mesa) if ped.modo == "mesa" else "Balcão")
                resposta_linhas.append(
                    f"• *Pedido #{ped.numero_pedido}* [{ped.status.upper()}] - {tipo_modo}\n"
                    f"  🛒 {itens_resumo} (R$ {ped.total:.2f})"
                )
            return {"status": "ok", "resposta": "\n".join(resposta_linhas)}

        # 2. Comando: 'cardapio'
        if texto == "cardapio":
            itens = listar_itens(db, empresa.id)
            if not itens:
                return {"status": "ok", "resposta": "🍔 O cardápio está vazio."}
                
            resposta_linhas = ["📋 *PRODUTOS DO CARDÁPIO:*"]
            for p in itens:
                status = "✅ Ativo" if p.disponivel else "❌ Pausado/Indisponível"
                resposta_linhas.append(f"• *{p.nome}* ({p.categoria}) - R$ {p.preco:.2f} | {status}")
            return {"status": "ok", "resposta": "\n".join(resposta_linhas)}

        # 3. Comando: 'pausar [item]'
        match_pausar = re.match(r'^pausar\s+(.+)$', texto)
        if match_pausar:
            item_nome = match_pausar.group(1).strip()
            item = obter_item_por_nome(db, empresa.id, item_nome)
            if not item:
                return {"status": "ok", "resposta": f"⚠️ Item '{item_nome}' não foi encontrado no cardápio."}
            item.disponivel = False
            db.commit()
            return {"status": "ok", "resposta": f"❌ *{item.nome}* foi pausado com sucesso e está indisponível para novos pedidos!"}

        # 4. Comando: 'ativar [item]'
        match_ativar = re.match(r'^ativar\s+(.+)$', texto)
        if match_ativar:
            item_nome = match_ativar.group(1).strip()
            item = obter_item_por_nome(db, empresa.id, item_nome)
            if not item:
                return {"status": "ok", "resposta": f"⚠️ Item '{item_nome}' não foi encontrado no cardápio."}
            item.disponivel = True
            db.commit()
            return {"status": "ok", "resposta": f"✅ *{item.nome}* foi ativado com sucesso e está disponível para novos pedidos!"}

        # 5. Comando: '[numero] tempo [minutos]' (ex: 42 tempo 20)
        match_tempo = re.match(r'^(\d+)\s+tempo\s+(\d+)$', texto)
        if match_tempo:
            num_pedido = int(match_tempo.group(1))
            tempo_min = int(match_tempo.group(2))
            
            pedido = obter_pedido_por_numero(db, empresa.id, num_pedido)
            if not pedido:
                return {"status": "ok", "resposta": f"⚠️ Pedido #{num_pedido} não foi encontrado."}
                
            # Atualizar status para 'em_preparo' se ainda estiver aguardando
            if pedido.status == "aguardando":
                pedido.status = "em_preparo"
                db.commit()
                
            # Notificar cliente do tempo estimado
            if pedido.lead_id:
                lead = db.query(Lead).filter(Lead.id == pedido.lead_id).first()
                if lead and lead.telefone:
                    config = empresa.configuracoes.config if empresa.configuracoes else {}
                    nome_agente = config.get("nome_agente", "Rosana")
                    msg_cliente = (
                        f"Olá! Aqui é o(a) {nome_agente} da Piccolo Lanches. 👋\n\n"
                        f"🍳 *Seu pedido #{pedido.numero_pedido} já está sendo preparado!*\n"
                        f"⏱️ O tempo estimado de preparo para o seu pedido é de *{tempo_min} minutos*.\n\n"
                        f"Assim que sair da nossa cozinha, te avisaremos aqui! 😊"
                    )
                    try:
                        enviar_whatsapp(lead.telefone, msg_cliente, empresa.evolution_instance)
                    except Exception as e:
                        logger.error(f"Erro ao notificar tempo ao cliente: {e}")
                        
            return {"status": "ok", "resposta": f"⏱️ Tempo de *{tempo_min} min* definido para o Pedido #{num_pedido} e cliente notificado!"}

        # 6. Comandos rápidos de status: '[numero] [status]' (ex: 42 ok, 42 pronto, 42 entregue, 42 cancela)
        match_status = re.match(r'^(\d+)\s+(ok|pronto|entregue|cancela|cancelado)$', texto)
        if match_status:
            num_pedido = int(match_status.group(1))
            cmd_status = match_status.group(2)
            
            pedido = obter_pedido_por_numero(db, empresa.id, num_pedido)
            if not pedido:
                return {"status": "ok", "resposta": f"⚠️ Pedido #{num_pedido} não foi encontrado."}
                
            # Mapear comando de texto para o status correto do BD
            status_map = {
                "ok": "em_preparo",
                "pronto": "pronto",
                "entregue": "entregue",
                "cancela": "cancelado",
                "cancelado": "cancelado"
            }
            novo_status = status_map[cmd_status]
            
            # Atualizar status (isso automaticamente dispara notificação simpática para o cliente no WhatsApp)
            atualizar_status_pedido(db, pedido.id, novo_status)
            
            status_emoji = {
                "em_preparo": "🍳 em preparo",
                "pronto": "✅ pronto",
                "entregue": "📦 finalizado/entregue",
                "cancelado": "❌ cancelado"
            }
            
            return {
                "status": "ok", 
                "resposta": f"🚀 Pedido #{num_pedido} atualizado para *{status_emoji[novo_status].upper()}* com sucesso!"
            }

        # 7. Resposta de ajuda caso não reconheça o comando
        resposta_ajuda = (
            "🤖 *Piccolo Lanchonete - Menu da Cozinha:*\n\n"
            "Comandos rápidos para gerenciar pedidos ativos:\n"
            "• `pedidos` (listar todos os pedidos ativos)\n"
            "• `[número] ok` (iniciar preparo do pedido)\n"
            "• `[número] tempo [minutos]` (ex: `42 tempo 25`)\n"
            "• `[número] pronto` (pedido pronto / motoboy)\n"
            "• `[número] entregue` (finalizar pedido)\n"
            "• `[número] cancela` (cancelar pedido)\n\n"
            "Comandos para controle de cardápio:\n"
            "• `cardapio` (listar cardápio completo)\n"
            "• `pausar [nome do item]` (ex: `pausar X-Burguer`)\n"
            "• `ativar [nome do item]` (ex: `ativar X-Burguer`)"
        )
        return {"status": "ok", "resposta": resposta_ajuda}

    except Exception as e:
        logger.error(f"Erro fatal na pipeline de comando da cozinha: {e}", exc_info=True)
        return {"status": "erro", "motivo": str(e)}
    finally:
        db.close()
