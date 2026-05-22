import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import Cardapio

def listar_itens(db: Session, empresa_id: uuid.UUID, apenas_disponiveis: bool = False) -> List[Cardapio]:
    """Retorna todos os itens de cardápio de uma empresa ordenados por categoria e ordem."""
    query = db.query(Cardapio).filter(Cardapio.empresa_id == empresa_id)
    if apenas_disponiveis:
        query = query.filter(Cardapio.disponivel == True)
    return query.order_by(Cardapio.categoria, Cardapio.ordem, Cardapio.nome).all()

def obter_item(db: Session, item_id: uuid.UUID) -> Optional[Cardapio]:
    """Obtém um item do cardápio pelo ID."""
    return db.query(Cardapio).filter(Cardapio.id == item_id).first()

def obter_item_por_nome(db: Session, empresa_id: uuid.UUID, nome: str) -> Optional[Cardapio]:
    """Obtém um item do cardápio pelo nome (case-insensitive)."""
    return db.query(Cardapio).filter(
        Cardapio.empresa_id == empresa_id,
        Cardapio.nome.ilike(nome.strip())
    ).first()

def adicionar_item(
    db: Session,
    empresa_id: uuid.UUID,
    categoria: str,
    nome: str,
    preco: float,
    descricao: Optional[str] = None,
    disponivel: bool = True,
    ordem: int = 0
) -> Cardapio:
    """Adiciona um novo item ao cardápio."""
    novo_item = Cardapio(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        categoria=categoria.strip(),
        nome=nome.strip(),
        descricao=descricao.strip() if descricao else None,
        preco=float(preco),
        disponivel=disponivel,
        ordem=ordem
    )
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)
    return novo_item

def atualizar_item(
    db: Session,
    item_id: uuid.UUID,
    categoria: Optional[str] = None,
    nome: Optional[str] = None,
    preco: Optional[float] = None,
    descricao: Optional[str] = None,
    disponivel: Optional[bool] = None,
    ordem: Optional[int] = None
) -> Optional[Cardapio]:
    """Atualiza os campos de um item existente."""
    item = obter_item(db, item_id)
    if not item:
        return None
        
    if categoria is not None:
        item.categoria = categoria.strip()
    if nome is not None:
        item.nome = nome.strip()
    if preco is not None:
        item.preco = float(preco)
    if descricao is not None:
        item.descricao = descricao.strip() if descricao else None
    if disponivel is not None:
        item.disponivel = disponivel
    if ordem is not None:
        item.ordem = ordem
        
    db.commit()
    db.refresh(item)
    return item

def toggle_disponibilidade(db: Session, item_id: uuid.UUID) -> Optional[Cardapio]:
    """Inverte o status de disponibilidade do item."""
    item = obter_item(db, item_id)
    if not item:
        return None
    item.disponivel = not item.disponivel
    db.commit()
    db.refresh(item)
    return item

def remover_item(db: Session, item_id: uuid.UUID) -> bool:
    """Remove um item do cardápio pelo ID."""
    item = obter_item(db, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
