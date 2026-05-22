from app.agents.triagem_agent import triagem_agent
from app.agents.contexto_agent import contexto_agent
from app.agents.especialistas import get_especialista
from app.openai_client import perguntar

CONTEXTO_AGUARDANDO_CONFIRMACAO = """
O cliente acabou de receber uma sugestão de falar com um atendente humano e você está
aguardando a confirmação dele.

Analise a mensagem do cliente:
- Se ele CONFIRMAR que quer falar com humano (sim, quero, pode chamar, por favor, etc.):
  Responda de forma acolhedora dizendo que já vai chamar um atendente, e inclua a tag [CONFIRMAR_TRANSBORDO]
  Exemplo: "Perfeito! Vou chamar um atendente agora mesmo para te ajudar. Um momento 🙂 [CONFIRMAR_TRANSBORDO]"

- Se ele RECUSAR ou mudar de assunto (não, pode continuar, deixa, tudo bem, etc.):
  Responda normalmente e retome o atendimento sem mencionar o transbordo novamente.
  Inclua a tag [CANCELAR_TRANSBORDO]
  Exemplo: "Claro, sem problema! Pode continuar, estou aqui para ajudar 😊 [CANCELAR_TRANSBORDO]"

Importante: sempre inclua uma das duas tags ([CONFIRMAR_TRANSBORDO] ou [CANCELAR_TRANSBORDO])
"""

def processar_mensagem_dinamica(
    mensagem_usuario: str,
    config: dict,
    intencao: str,       # mantido por compatibilidade
    stage: str,          # mantido por compatibilidade
    contexto_tempo: str, # mantido por compatibilidade
    historico=None,
    sentimento: str = "neutro",
    empresa=None,
    lead=None,
    lead_seguro=None,
    documentos_legais=None
):
    """
    Mantém a assinatura atual para não quebrar o pipeline.
    Delegado para a nova arquitetura modular de múltiplos agentes.
    """
    # 1. Simular / preencher triagem se não passou
    triagem = {
        "intencao": intencao,
        "sentimento": sentimento,
        "urgente": False,
        "resumo_curto": ""
    }

    # 2. Montar contexto estruturado
    class MockObj:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_empresa = empresa or MockObj(nome=config.get("nome_empresa", "Empresa"), nicho=config.get("nicho", "generico"))
    mock_lead = lead or MockObj(id=None, telefone=None, stage=stage, nome=None)

    ctx = contexto_agent.montar(
        empresa=mock_empresa,
        lead=mock_lead,
        lead_seguro=lead_seguro,
        triagem=triagem,
        config=config,
        documentos_legais=documentos_legais
    )

    # 3. Chamar especialista do nicho
    nicho = config.get("nicho", "generico")
    especialista = get_especialista(nicho)
    return especialista.processar(mensagem_usuario, ctx, historico or [])

def processar_confirmacao_transbordo(mensagem_usuario: str, historico=None):
    """Usado quando o número está em status 'aguardando' - decide se confirma ou cancela."""
    return perguntar(mensagem_usuario, CONTEXTO_AGUARDANDO_CONFIRMACAO, historico)