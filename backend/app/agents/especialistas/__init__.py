from app.agents.base_agent import BaseAgent
from .generico import EspecialistaGenerico
from .corretora import EspecialistaCorretora
from .contabilidade import EspecialistaContabilidade

_ESPECIALISTAS = {
    "generico": EspecialistaGenerico(),
    "academia": EspecialistaGenerico(),   # utiliza o especialista genérico
    "corretora": EspecialistaCorretora(),
    "contabilidade": EspecialistaContabilidade(),
}

def get_especialista(nicho: str) -> BaseAgent:
    """
    Retorna o especialista correto para o nicho.
    Fallback para genérico se o nicho não for mapeado.
    """
    return _ESPECIALISTAS.get(nicho, _ESPECIALISTAS["generico"])
