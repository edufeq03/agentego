import re
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal, Lead, Mensagem, Empresa, Cardapio
from app.agents.especialistas import get_especialista
from app.cardapio_service import listar_itens, obter_item_por_nome
from app.pedido_service import criar_pedido, notificar_cozinha, obter_comanda_aberta, fechar_comanda

logger = logging.getLogger(__name__)

def formatar_cardapio_para_ia(itens: list) -> str:
    """Formata a lista de itens de cardápio do banco em um texto legível para a IA."""
    if not itens:
        return "Nenhum item cadastrado no cardápio no momento."
        
    categorias = {}
    for item in itens:
        cat = item.categoria
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(item)
        
    cardapio_linhas = []
    for cat, pratos in categorias.items():
        cardapio_linhas.append(f"\n=== {cat.upper()} ===")
        for p in pratos:
            status_disp = "" if p.disponivel else " [INDISPONÍVEL NO MOMENTO]"
            desc = f" ({p.descricao})" if p.descricao else ""
            cardapio_linhas.append(f"• *{p.nome}* - R$ {p.preco:.2f}{desc}{status_disp}")
            
    return "\n".join(cardapio_linhas)

def processar_pipeline_lanchonete(empresa: Empresa, telefone: str, mensagem_texto: str) -> dict:
    """
    Pipeline exclusivo para o nicho de Lanchonete.
    Gerencia a máquina de estados do pedido e interpreta as escolhas do cliente.
    """
    db = SessionLocal()
    try:
        # 0. GUARDRAIL: Modo de Recepção de Contatos (importado do pipeline central)
        from app.pipeline import _verificar_guardrails
        guardrails_resultado = _verificar_guardrails(db, empresa, telefone)
        if guardrails_resultado:
            if guardrails_resultado["status"] == "ignorado":
                return guardrails_resultado
            # status == "retomar": atendimento liberado, mas sem apresentação formal
        is_retomar = guardrails_resultado is not None and guardrails_resultado.get("status") == "retomar"

        # 1. Carregar/Criar Lead
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone).first()
        if not lead:
            lead = Lead(empresa_id=empresa.id, telefone=telefone, stage="novo")
            db.add(lead)
            db.commit()
            db.refresh(lead)

        # 2. Inicializar dados customizados do pedido no Lead se não existirem
        dados_custom = lead.dados_customizados or {}
        if not isinstance(dados_custom, dict):
            dados_custom = {}
            
        # Parâmetros padrão do pedido
        pedido_estado = dados_custom.get("pedido_estado", "inicio")
        pedido_modo = dados_custom.get("pedido_modo", None)
        pedido_mesa = dados_custom.get("pedido_mesa", None)
        pedido_endereco = dados_custom.get("pedido_endereco", None)
        pedido_nome_balcao = dados_custom.get("pedido_nome_balcao", None)
        pedido_itens = dados_custom.get("pedido_itens", []) # [{"nome": ..., "preco_unit": ..., "quantidade": ..., "obs": ...}]
        
        # 3. Registrar a mensagem do usuário no banco
        msg_usuario = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead.id,
            tipo="usuario",
            mensagem=mensagem_texto,
            timestamp=datetime.utcnow()
        )
        db.add(msg_usuario)
        db.commit()

        # 4. Carregar o cardápio disponível da empresa
        itens_cardapio = listar_itens(db, empresa.id, apenas_disponiveis=True)
        cardapio_formatado = formatar_cardapio_para_ia(itens_cardapio)

        # 5. Montar o histórico recente para a IA (últimas 6 mensagens)
        historico_db = db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.desc()).limit(6).all()
        historico = []
        for m in reversed(historico_db):
            # Ignora a mensagem que acabamos de receber
            if m.id != msg_usuario.id:
                role = "user" if m.tipo == "usuario" else "assistant"
                historico.append({"role": role, "content": m.mensagem})

        # 6. Preparar o contexto do agente
        config_dict = empresa.configuracoes.config if empresa.configuracoes else {}
        nome_agente = config_dict.get("nome_agente", "Rosana")
        modo_comanda_aberta = config_dict.get("modo_comanda_aberta", False)
        
        # Modo de Recepção: injeta flag para omitir apresentação formal para contatos conhecidos
        if is_retomar:
            config_dict["_retomar_sem_apresentacao"] = True
            
        # Comanda Aberta (Buscar histórico de pedidos pendentes de pagamento do lead)
        comanda_aberta_str = ""
        if modo_comanda_aberta:
            pedidos_comanda = obter_comanda_aberta(db, empresa.id, lead.id)
            if pedidos_comanda:
                linhas_comanda = []
                total_comanda = 0.0
                for ped in pedidos_comanda:
                    for it in ped.itens:
                        linhas_comanda.append(f"- {it.quantidade}x {it.nome} (R$ {it.preco_unit:.2f})")
                    total_comanda += ped.total
                comanda_aberta_str = "=== CONTA ABERTA ATUAL ===\nO cliente já consumiu e mandou para a cozinha os seguintes itens:\n" + "\n".join(linhas_comanda) + f"\nTotal Parcial: R$ {total_comanda:.2f}\n"
        
        dados_pedido_ctx = {
            "estado": pedido_estado,
            "modo": pedido_modo or "Não definido",
            "mesa": pedido_mesa,
            "endereco": pedido_endereco,
            "nome_balcao": pedido_nome_balcao,
            "itens": pedido_itens
        }
        
        contexto_agente = {
            "config": config_dict,
            "nome_agente": nome_agente,
            "nome_empresa": empresa.nome,
            "contexto_tempo": f"Data/Hora Atual: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "intencao": "pedido",
            "stage": lead.stage,
            "sentimento": "positivo",
            "cardapio_formatado": cardapio_formatado,
            "dados_pedido": dados_pedido_ctx,
            "comanda_aberta_str": comanda_aberta_str
        }

        # 7. Chamar o especialista de Lanchonete
        especialista = get_especialista("lanchonete")
        resposta_raw, t_in, t_out = especialista.processar(mensagem_texto, contexto_agente, historico)

        # 8. Atualizar custos de tokens
        empresa.tokens_input_mes = (empresa.tokens_input_mes or 0) + t_in
        empresa.tokens_output_mes = (empresa.tokens_output_mes or 0) + t_out
        db.commit()

        # 9. Interpretar tags técnicas retornadas pela IA
        logger.info(f"[{telefone}] Resposta crua da IA: {resposta_raw}")
        
        # A. [DEFINIR_MODO: modo=...]
        match_modo = re.search(r'\[DEFINIR_MODO:\s*modo=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        if match_modo:
            modo_val = match_modo.group(1).strip().lower()
            if modo_val in ("delivery", "balcao", "mesa"):
                pedido_modo = modo_val
                pedido_estado = "montando"
                logger.info(f"[{telefone}] Estado transitado para: montando (Modo: {pedido_modo})")
                
        # B. [ATUALIZAR_LEAD: mesa=...] ou [ATUALIZAR_LEAD: endereco=...]
        tags_atualizar = re.findall(r'\[ATUALIZAR_LEAD:\s*([^\]]+)\]', resposta_raw)
        for tag in tags_atualizar:
            if '=' in tag:
                k, v = tag.split('=', 1)
                k = k.strip().lower()
                v = v.strip()
                if k == "mesa":
                    pedido_mesa = int(v) if v.isdigit() else v
                elif k == "endereco":
                    pedido_endereco = v
                elif k == "nome_balcao":
                    pedido_nome_balcao = v

        # C. [ADICIONAR_ITEM: ...]
        tags_adicionar = re.findall(r'\[ADICIONAR_ITEM:\s*([^\]]+)\]', resposta_raw, re.IGNORECASE)
        for tag in tags_adicionar:
            # Parsear parâmetros separados por vírgula (ex: nome=X-Burguer, quantidade=2, obs=sem cebola)
            params = {}
            for part in tag.split(','):
                if '=' in part:
                    pk, pv = part.split('=', 1)
                    params[pk.strip().lower()] = pv.strip()
                    
            item_nome = params.get("nome")
            item_qtd_str = params.get("quantidade", "1")
            item_qtd = int(item_qtd_str) if item_qtd_str.isdigit() else 1
            item_obs = params.get("obs", "")
            
            if item_nome:
                # Verificar se o item existe no cardápio
                prato = obter_item_por_nome(db, empresa.id, item_nome)
                if prato and prato.disponivel:
                    # Checar se já existe no carrinho para acumular
                    ja_existe = False
                    for pit in pedido_itens:
                        if pit["nome"].lower() == prato.nome.lower() and pit.get("obs", "") == item_obs:
                            pit["quantidade"] += item_qtd
                            ja_existe = True
                            break
                    if not ja_existe:
                        pedido_itens.append({
                            "cardapio_id": str(prato.id),
                            "nome": prato.nome,
                            "preco_unit": prato.preco,
                            "quantidade": item_qtd,
                            "obs": item_obs
                        })
                    logger.info(f"[{telefone}] Item adicionado: {item_nome} x{item_qtd}")

        # D. [REMOVER_ITEM: nome=...]
        tags_remover = re.findall(r'\[REMOVER_ITEM:\s*nome=([^\]]+)\]', resposta_raw, re.IGNORECASE)
        for r_nome in tags_remover:
            r_nome = r_nome.strip().lower()
            pedido_itens = [pit for pit in pedido_itens if pit["nome"].lower() != r_nome]
            logger.info(f"[{telefone}] Item removido: {r_nome}")

        # E. [SOLICITAR_CONFIRMACAO]
        if "[SOLICITAR_CONFIRMACAO]" in resposta_raw or "confirma esse pedido" in resposta_raw.lower() or "Você confirma" in resposta_raw or "Total geral:" in resposta_raw:
            pedido_estado = "confirmando"
            logger.info(f"[{telefone}] Estado transitado para: confirmando (Tag ou Heurística)")

        # F. [CONFIRMAR_PEDIDO]
        pedido_criado_numero = None
        if "[CONFIRMAR_PEDIDO]" in resposta_raw or (pedido_estado == "confirmando" and ("confirmado" in resposta_raw.lower() or "pedido foi" in resposta_raw.lower() or "cozinha" in resposta_raw.lower())):
            if pedido_itens:
                # Calcular total geral do pedido
                total_itens = sum(it["preco_unit"] * it["quantidade"] for it in pedido_itens)
                taxa_entrega = config_dict.get("taxa_entrega", 0.0) if pedido_modo == "delivery" else 0.0
                total_geral = total_itens + taxa_entrega
                
                # Criar o pedido no banco
                pedido_db = criar_pedido(
                    db=db,
                    empresa_id=empresa.id,
                    lead_id=lead.id,
                    modo=pedido_modo or "balcao",
                    total=total_geral,
                    itens=pedido_itens,
                    observacao=dados_custom.get("observacao_pedido_geral"),
                    endereco=pedido_endereco,
                    nome_balcao=pedido_nome_balcao or lead.nome,
                    numero_mesa=pedido_mesa if isinstance(pedido_mesa, int) else None
                )
                pedido_criado_numero = pedido_db.numero_pedido
                
                # Notificar a cozinha imediatamente!
                notificar_cozinha(db, empresa, pedido_db)
                
                # Resetar carrinho do lead baseado no modo
                if modo_comanda_aberta:
                    pedido_estado = "montando" # Volta para montando para continuar pedindo
                    pedido_itens = []
                    # Mantem o modo, mesa, endereco, etc
                    logger.info(f"[{telefone}] Pedido Parcial #{pedido_criado_numero} enviado p/ cozinha. Comanda continua aberta.")
                else:
                    pedido_estado = "pedido_feito"
                    pedido_itens = []
                    pedido_modo = None
                    pedido_mesa = None
                    pedido_endereco = None
                    pedido_nome_balcao = None
                    
                dados_custom.pop("observacao_pedido_geral", None)
            else:
                logger.warning(f"[{telefone}] Tentou confirmar pedido com carrinho vazio!")

        # F2. [FECHAR_CONTA] (Apenas p/ Modo Comanda Aberta)
        conta_fechada_total = None
        if "[FECHAR_CONTA]" in resposta_raw and modo_comanda_aberta:
            pedidos_comanda = obter_comanda_aberta(db, empresa.id, lead.id)
            if pedidos_comanda:
                conta_fechada_total = sum(p.total for p in pedidos_comanda)
                fechar_comanda(db, empresa.id, lead.id)
                logger.info(f"[{telefone}] Conta fechada! Total: R$ {conta_fechada_total:.2f}")
                
            # Zera o estado do cliente totalmente
            pedido_estado = "pedido_feito"
            pedido_itens = []
            pedido_modo = None
            pedido_mesa = None
            pedido_endereco = None
            pedido_nome_balcao = None
            dados_custom.pop("observacao_pedido_geral", None)

        # G. [SALVAR_AVALIACAO: nota=..., comentario=...]
        match_avaliacao = re.search(r'\[SALVAR_AVALIACAO:\s*nota=([^,\]]+)(?:,\s*comentario=([^\]]+))?\]', resposta_raw, re.IGNORECASE)
        if match_avaliacao:
            nota_val = match_avaliacao.group(1).strip()
            comentario_val = match_avaliacao.group(2).strip() if match_avaliacao.group(2) else ""
            
            # Tentar achar o último pedido deste lead que não foi cancelado
            from app.database import Pedido
            ultimo_pedido = db.query(Pedido).filter(
                Pedido.empresa_id == empresa.id,
                Pedido.lead_id == lead.id,
                Pedido.status != "cancelado"
            ).order_by(Pedido.criado_em.desc()).first()
            
            if ultimo_pedido:
                try:
                    ultimo_pedido.avaliacao_nota = int(nota_val)
                    ultimo_pedido.avaliacao_comentario = comentario_val
                    db.commit()
                    logger.info(f"[{telefone}] Avaliação salva no Pedido #{ultimo_pedido.numero_pedido}: Nota={nota_val}, Comentário={comentario_val}")
                except ValueError:
                    logger.error(f"[{telefone}] Erro ao converter nota de avaliação: {nota_val}")
            else:
                logger.warning(f"[{telefone}] Avaliação recebida, mas nenhum pedido encontrado para o lead.")

        # 10. Atualizar o lead com o novo estado do carrinho
        dados_custom["pedido_estado"] = pedido_estado
        dados_custom["pedido_modo"] = pedido_modo
        dados_custom["pedido_mesa"] = pedido_mesa
        dados_custom["pedido_endereco"] = pedido_endereco
        dados_custom["pedido_nome_balcao"] = pedido_nome_balcao
        dados_custom["pedido_itens"] = pedido_itens
        
        lead.dados_customizados = dados_custom
        flag_modified(lead, "dados_customizados")
        db.commit()

        # 11. Limpar as tags técnicas do texto de resposta do cliente
        resposta_limpa = resposta_raw
        for tag in ("[SOLICITAR_CONFIRMACAO]", "[CONFIRMAR_PEDIDO]", "[FECHAR_CONTA]"):
            resposta_limpa = resposta_limpa.replace(tag, "").strip()
            
        resposta_limpa = re.sub(r'\[DEFINIR_MODO:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[ATUALIZAR_LEAD:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[ADICIONAR_ITEM:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[REMOVER_ITEM:[^\]]*\]', '', resposta_limpa)
        resposta_limpa = re.sub(r'\[SALVAR_AVALIACAO:[^\]]*\]', '', resposta_limpa)
        
        resposta_limpa = resposta_limpa.strip()
        
        # Customização para o estado de 'pedido_feito' informando o número gerado
        if pedido_criado_numero is not None:
            resposta_limpa += f"\n\n👉 *O número do seu pedido é: #{pedido_criado_numero}*."

        # 12. Salvar resposta da IA no banco
        msg_agente = Mensagem(
            empresa_id=empresa.id,
            lead_id=lead.id,
            tipo="agente",
            mensagem=resposta_limpa,
            timestamp=datetime.utcnow()
        )
        db.add(msg_agente)
        db.commit()

        return {"status": "ok", "resposta": resposta_limpa}
        
    except Exception as e:
        logger.error(f"Erro no processamento da pipeline_lanchonete: {e}", exc_info=True)
        return {"status": "erro", "motivo": str(e)}
    finally:
        db.close()
