from app.agents.base_agent import BaseAgent
from .generico import EspecialistaGenerico
from .corretora import EspecialistaCorretora
from .contabilidade import EspecialistaContabilidade
from .lanchonete import EspecialistaLanchonete
from .agenda import EspecialistaAgenda
from .beleza import EspecialistaBeleza

_ESPECIALISTAS = {
    "generico": EspecialistaGenerico(),
    "academia": EspecialistaGenerico(),   # utiliza o especialista genérico
    "corretora": EspecialistaCorretora(),
    "contabilidade": EspecialistaContabilidade(),
    "lanchonete": EspecialistaLanchonete(),
    "agenda": EspecialistaAgenda(),
    "higienizacao": EspecialistaAgenda(),
    "beleza": EspecialistaBeleza(),
}

def get_especialista(nicho: str) -> BaseAgent:
    """
    Retorna o especialista correto para o nicho.
    Fallback para genérico se o nicho não for mapeado.
    """
    return _ESPECIALISTAS.get(nicho, _ESPECIALISTAS["generico"])
