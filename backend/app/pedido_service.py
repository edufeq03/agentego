import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import Pedido, ItemPedido, Empresa, Lead, FollowupDelivery
from app.whatsapp import enviar_whatsapp
from datetime import datetime, timedelta

def criar_pedido(
    db: Session,
    empresa_id: uuid.UUID,
    lead_id: Optional[uuid.UUID],
    modo: str, # 'delivery', 'balcao', 'mesa'
    total: float,
    itens: List[Dict[str, Any]], # [{"cardapio_id": ..., "nome": ..., "preco_unit": ..., "quantidade": ..., "observacao": ...}]
    observacao: Optional[str] = None,
    endereco: Optional[str] = None,
    nome_balcao: Optional[str] = None,
    numero_mesa: Optional[int] = None
) -> Pedido:
    """Cria um novo pedido com número sequencial por empresa e seus respectivos itens."""
    # 1. Calcular próximo número sequencial de pedido para esta empresa
    max_num = db.query(func.max(Pedido.numero_pedido)).filter(Pedido.empresa_id == empresa_id).scalar()
    novo_numero = (max_num or 0) + 1
    
    # 2. Criar cabeçalho do pedido
    pedido = Pedido(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        lead_id=lead_id,
        numero_pedido=novo_numero,
        modo=modo,
        status="aguardando",
        total=float(total),
        observacao=observacao.strip() if observacao else None,
        endereco=endereco.strip() if endereco else None,
        nome_balcao=nome_balcao.strip() if nome_balcao else None,
        numero_mesa=numero_mesa,
        pagamento_status="pendente"
    )
    db.add(pedido)
    db.flush() # Gera o ID do pedido para associar nos itens
    
    # 3. Adicionar itens do pedido
    for item in itens:
        item_pedido = ItemPedido(
            id=uuid.uuid4(),
            pedido_id=pedido.id,
            cardapio_id=item.get("cardapio_id"),
            nome=item["nome"].strip(),
            preco_unit=float(item["preco_unit"]),
            quantidade=int(item["quantidade"]),
            observacao=item.get("observacao")
        )
        db.add(item_pedido)
        
    db.commit()
    db.refresh(pedido)
    return pedido

def obter_pedido(db: Session, pedido_id: uuid.UUID) -> Optional[Pedido]:
    """Retorna um pedido específico pelo ID."""
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def obter_pedido_por_numero(db: Session, empresa_id: uuid.UUID, numero: int) -> Optional[Pedido]:
    """Retorna um pedido específico pelo número sequencial da empresa."""
    return db.query(Pedido).filter(
        Pedido.empresa_id == empresa_id,
        Pedido.numero_pedido == numero
    ).first()

def obter_pedidos_ativos(db: Session, empresa_id: uuid.UUID) -> List[Pedido]:
    """Retorna os pedidos ativos da empresa (diferentes de 'entregue' e 'cancelado')."""
    return db.query(Pedido).filter(
        Pedido.empresa_id == empresa_id,
        Pedido.status.notin_(["entregue", "cancelado"])
    ).order_by(Pedido.criado_em.asc()).all()

def obter_historico_pedidos(
    db: Session,
    empresa_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Pedido]:
    """Retorna o histórico de pedidos da empresa."""
    query = db.query(Pedido).filter(Pedido.empresa_id == empresa_id)
    if status:
        query = query.filter(Pedido.status == status)
    return query.order_by(Pedido.criado_em.desc()).limit(limit).offset(offset).all()

def obter_comanda_aberta(db: Session, empresa_id: uuid.UUID, lead_id: uuid.UUID) -> List[Pedido]:
    """Retorna todos os pedidos da comanda aberta (pagamento pendente) do cliente."""
    return db.query(Pedido).filter(
        Pedido.empresa_id == empresa_id,
        Pedido.lead_id == lead_id,
        Pedido.pagamento_status == "pendente",
        Pedido.status.notin_(["cancelado"])
    ).order_by(Pedido.criado_em.asc()).all()

def fechar_comanda(db: Session, empresa_id: uuid.UUID, lead_id: uuid.UUID) -> None:
    """Marca todos os pedidos com pagamento pendente como pagos (fecha a conta)."""
    pedidos_pendentes = obter_comanda_aberta(db, empresa_id, lead_id)
    for p in pedidos_pendentes:
        p.pagamento_status = "pago"
    db.commit()

def atualizar_status_pedido(db: Session, pedido_id: uuid.UUID, novo_status: str) -> Optional[Pedido]:
    """Atualiza o status de um pedido e envia notificações automáticas."""
    pedido = obter_pedido(db, pedido_id)
    if not pedido:
        return None
        
    pedido.status = novo_status
    db.commit()
    db.refresh(pedido)
    
    # 1. Carregar a empresa para enviar as notificações
    empresa = db.query(Empresa).filter(Empresa.id == pedido.empresa_id).first()
    if empresa:
        # Notificar o cliente sobre a mudança de status
        notificar_cliente_status(db, empresa, pedido)
        
        # 2. Agendar pesquisa de satisfação se for entregue e configurado
        if novo_status == "entregue":
            config = empresa.configuracoes.config if empresa.configuracoes else {}
            if config.get("habilitar_pesquisa_satisfacao"):
                lead = db.query(Lead).filter(Lead.id == pedido.lead_id).first()
                if lead and lead.telefone:
                    tempo_minutos = int(config.get("tempo_pesquisa_minutos", 60))
                    agendado = datetime.utcnow() + timedelta(minutes=tempo_minutos)
                    
                    novo_followup = FollowupDelivery(
                        empresa_id=empresa.id,
                        pedido_id=pedido.id,
                        telefone=lead.telefone,
                        agendado_para=agendado
                    )
                    db.add(novo_followup)
                    db.commit()
                    print(f"Followup de pesquisa agendado para o pedido {pedido.numero_pedido} às {agendado}")
        
    return pedido

def notificar_cozinha(db: Session, empresa: Empresa, pedido: Pedido):
    """Envia uma notificação formatada do novo pedido para o WhatsApp da Cozinha."""
    config = empresa.configuracoes.config if empresa.configuracoes else {}
    tel_cozinha = config.get("whatsapp_cozinha")
    if not tel_cozinha:
        print(f"Aviso: whatsapp_cozinha não configurado para a empresa {empresa.nome}")
        return
        
    # Normalizar telefone
    tel_cozinha = "".join(filter(str.isdigit, str(tel_cozinha)))
    if not tel_cozinha:
        return
    if len(tel_cozinha) in (10, 11):
        tel_cozinha = "55" + tel_cozinha

    # Obter nome do lead
    nome_cliente = "Cliente"
    telefone_cliente = "Não informado"
    if pedido.lead_id:
        lead = db.query(Lead).filter(Lead.id == pedido.lead_id).first()
        if lead:
            nome_cliente = lead.nome or "Cliente"
            telefone_cliente = lead.telefone
            
    # Formatar itens
    itens_str = ""
    for item in pedido.itens:
        obs_str = f" (Obs: {item.observacao})" if item.observacao else ""
        itens_str += f"• {item.quantidade}x *{item.nome}* - R$ {item.preco_unit * item.quantidade:.2f}{obs_str}\n"
        
    # Detalhes do modo
    detalhes_modo = ""
    if pedido.modo == "delivery":
        detalhes_modo = f"🛵 *Entrega (Delivery):*\n📍 Endereço: {pedido.endereco or 'Não informado'}"
    elif pedido.modo == "mesa":
        detalhes_modo = f"🍽️ *Consumo na Mesa:*\n📌 Mesa nº: {pedido.numero_mesa or 'Mesa não informada'}"
    else:
        detalhes_modo = f"🛍️ *Retirada no Balcão:*\n👤 Nome: {pedido.nome_balcao or nome_cliente}"

    mensagem = (
        f"🔔 *NOVO PEDIDO RECEBIDO!* 🔔\n\n"
        f"📝 *Pedido #{pedido.numero_pedido}*\n"
        f"👤 Cliente: {nome_cliente} ({telefone_cliente})\n"
        f"🕒 Horário: {pedido.criado_em.strftime('%d/%m %H:%M')}\n\n"
        f"🛒 *ITENS DO PEDIDO:*\n"
        f"{itens_str}\n"
        f"💰 *Total Geral:* R$ {pedido.total:.2f}\n\n"
        f"{detalhes_modo}\n"
        f"💬 Obs Geral: {pedido.observacao or 'Nenhuma'}\n\n"
        f"⚡ *Comandos Rápidos de Cozinha:*\n"
        f"• `{pedido.numero_pedido} ok` (iniciar preparo)\n"
        f"• `{pedido.numero_pedido} pronto` (marcar como pronto)\n"
        f"• `{pedido.numero_pedido} entregue` (finalizar)\n"
        f"• `{pedido.numero_pedido} cancela` (cancelar)"
    )
    
    try:
        enviar_whatsapp(tel_cozinha, mensagem, empresa.evolution_instance)
        print(f"Cozinha notificada sobre o Pedido #{pedido.numero_pedido}")
    except Exception as e:
        print(f"Erro ao notificar cozinha no WhatsApp: {e}")

def notificar_cliente_status(db: Session, empresa: Empresa, pedido: Pedido):
    """Envia uma atualização simpática de status para o cliente via WhatsApp."""
    if not pedido.lead_id:
        return
        
    lead = db.query(Lead).filter(Lead.id == pedido.lead_id).first()
    if not lead or not lead.telefone:
        return
        
    config = empresa.configuracoes.config if empresa.configuracoes else {}
    nome_agente = config.get("nome_agente", "Rosana")
    
    # Mapear status para mensagens simpáticas
    mensagens_status = {
        "em_preparo": (
            f"🍳 *Seu pedido #{pedido.numero_pedido} está em preparo!*\n\n"
            f"Nossa cozinha já está preparando suas delícias com muito carinho. "
            f"Em instantes voltamos com mais novidades! 😋"
        ),
        "pronto": {
            "delivery": (
                f"🛵 *Seu pedido #{pedido.numero_pedido} está pronto e saiu para entrega!*\n\n"
                f"O entregador já está a caminho com o seu pedido quentinho. Prepare a mesa! 🎉"
            ),
            "mesa": (
                f"🍽️ *Seu pedido #{pedido.numero_pedido} está pronto e sendo servido na sua mesa!*\n\n"
                f"Bom apetite! Se precisar de algo mais, é só chamar. 😋"
            ),
            "balcao": (
                f"🛍️ *Seu pedido #{pedido.numero_pedido} está pronto para retirada!*\n\n"
                f"Você já pode vir até o nosso balcão retirar o seu pedido quentinho. Esperamos você!"
            )
        },
        "entregue": (
            f"✅ *Seu pedido #{pedido.numero_pedido} foi entregue/finalizado!*\n\n"
            f"Muito obrigado pela preferência e confiança. "
            f"Esperamos que tenha uma experiência fantástica! Se puder, nos conte o que achou! ❤️"
        ),
        "cancelado": (
            f"❌ *Informação importante sobre o pedido #{pedido.numero_pedido}*\n\n"
            f"Lamentamos informar que o seu pedido foi cancelado. "
            f"Se você não solicitou o cancelamento ou gostaria de entender o motivo, por favor nos responda aqui para te auxiliarmos."
        )
    }
    
    # Tratar caso especial de 'pronto' que depende do modo
    if pedido.status == "pronto":
        msg = mensagens_status["pronto"].get(pedido.modo, mensagens_status["pronto"]["balcao"])
    else:
        msg = mensagens_status.get(pedido.status)
        
    if not msg:
        return
        
    mensagem_final = (
        f"Olá! Aqui é o(a) {nome_agente} da Piccolo Lanches. 👋\n\n"
        f"{msg}"
    )
    
    try:
        enviar_whatsapp(lead.telefone, mensagem_final, empresa.evolution_instance)
        print(f"Cliente {lead.telefone} notificado: status={pedido.status}")
    except Exception as e:
        print(f"Erro ao notificar cliente no WhatsApp: {e}")
