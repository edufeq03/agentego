from .base import Base, get_db, engine, SessionLocal
from .tenant import Empresa, Usuario, CodigoRecuperacao, Configuracao, PromptTemplate
from .atendimento import Lead, Mensagem, Evento, Transbordo, EstadoAuxiliar, CampoCustomizado
from .marketing import Campanha, Comunicado, ComunicadoLog, ListaTransmissao, ListaTransmissaoContato, DisparoLista
from .agenda import Servico, Disponibilidade, Bloqueio, Agendamento, ItemAgendamento, ListaEspera, SerieRecorrencia
from .lanchonete import Cardapio, Pedido, ItemPedido, FollowupDelivery
from .seguro import LeadSeguro, DocumentoSeguro, FollowupSeguro
from .contabilidade import EmpresaCliente, ObrigacaoFiscal, DocumentoLegal
from .viagens import ClienteAgenciaViagens
from .academia import MembroAcademia
from .crm import (
    CrmContact, CrmOrganization, CrmContactOrganization, CrmPipeline, 
    CrmDeal, CrmActivity, CrmContext, CrmAuditLog
)

__all__ = [
    "Base", "get_db", "engine", "SessionLocal",
    "Empresa", "Usuario", "CodigoRecuperacao", "Configuracao", "PromptTemplate",
    "Lead", "Mensagem", "Evento", "Transbordo", "EstadoAuxiliar", "CampoCustomizado",
    "Campanha", "Comunicado", "ComunicadoLog", "ListaTransmissao", "ListaTransmissaoContato", "DisparoLista",
    "Servico", "Disponibilidade", "Bloqueio", "Agendamento", "ItemAgendamento", "ListaEspera", "SerieRecorrencia",
    "Cardapio", "Pedido", "ItemPedido", "FollowupDelivery",
    "LeadSeguro", "DocumentoSeguro", "FollowupSeguro",
    "EmpresaCliente", "ObrigacaoFiscal", "DocumentoLegal",
    "ClienteAgenciaViagens",
    "MembroAcademia",
    "CrmContact", "CrmOrganization", "CrmContactOrganization", "CrmPipeline", 
    "CrmDeal", "CrmActivity", "CrmContext", "CrmAuditLog"
]
