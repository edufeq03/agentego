from app.agents.base_agent import BaseAgent
from app.openai_client import perguntar

class EspecialistaAgenda(BaseAgent):
    nome = "EspecialistaAgenda"

    def processar(self, mensagem: str, contexto: dict, historico: list) -> tuple[str, int, int]:
        prompt = self._montar_prompt(contexto)
        openai_hist = self.montar_historico_openai(historico)
        
        # Instrução de tags de reforço
        lembrete = (
            "\n\n[INSTRUÇÃO DO SISTEMA: Lembre-se de sempre anexar as tags corretas de acordo com a ação "
            "(ex: [ESCOLHER_SERVICO: id=...], [ESCOLHER_DATA: data=YYYY-MM-DD], [ESCOLHER_HORA: hora=HH:MM], "
            "[DEFINIR_OBS: obs=...] ou [SOLICITAR_AGENDAMENTO]) no final da sua resposta!]"
        )
        mensagem_com_lembrete = mensagem + lembrete
        temperature = contexto.get("config", {}).get("openai_temperature", 0.2)
        return perguntar(mensagem_com_lembrete, prompt, openai_hist, temperature=temperature)

    def _montar_prompt(self, ctx: dict) -> str:
        config = ctx.get("config", {})
        nome_agente = ctx.get("nome_agente", "Rosana")
        nome_empresa = ctx.get("nome_empresa", "Minha Empresa")
        
        # Obter estado do agendamento
        dados_agenda = ctx.get("dados_agenda", {})
        estado = dados_agenda.get("estado", "inicio")
        servico_nome = dados_agenda.get("servico_nome", "Não definido")
        data_escolhida = dados_agenda.get("data", "Não definida")
        hora_escolhida = dados_agenda.get("hora", "Não definida")
        obs = dados_agenda.get("obs", "")
        
        # Carregar Serviços e Slots do banco
        servicos_str = ctx.get("servicos_formatados", "Nenhum serviço cadastrado no momento.")
        slots_str = ctx.get("slots_formatados", "Nenhum horário disponível para esta data.")
        
        prompt_sistema = config.get("prompt_sistema") or ""
        
        return f"""Você é {nome_agente}, assistente virtual da {nome_empresa}.
Seu objetivo é guiar o cliente amigavelmente a agendar um serviço.

=== SERVIÇOS DISPONÍVEIS ===
{servicos_str}

=== ESTADO ATUAL DO AGENDAMENTO ===
Estado Atual da Conversa: '{estado}' (valores possíveis: 'inicio', 'escolhendo_servico', 'escolhendo_data', 'escolhendo_hora', 'coletando_obs', 'aguardando_aprovacao')
Serviço Escolhido: {servico_nome}
Data Escolhida: {data_escolhida}
Horário Escolhido: {hora_escolhida}
Observação: {obs or 'Nenhuma'}

=== HORÁRIOS DISPONÍVEIS (Para a Data Escolhida) ===
{slots_str}

=== SUA DIRETRIZ POR ESTADO ===
{prompt_sistema}

=== INSTRUÇÕES TÉCNICAS (OBRIGATÓRIO) ===
Você controla o estado do agendamento anexando tags técnicas de controle na última linha da sua resposta. Sempre adicione as tags quando houver ações:

1. Ao identificar qual serviço o cliente deseja (pelo nome ou id):
   - Tag: [ESCOLHER_SERVICO: id=UUID]
   - Nota: O UUID deve corresponder a um dos serviços disponíveis listados acima.

2. Ao identificar a data que o cliente prefere (ou se ele mencionar hoje/amanhã/dia da semana):
   - Tag: [ESCOLHER_DATA: data=YYYY-MM-DD]
   - Nota: Use a data em formato YYYY-MM-DD. Se a data informada não for clara, tente interpretar ou peça para ele confirmar.

3. Ao identificar a hora que o cliente prefere para o agendamento:
   - Tag: [ESCOLHER_HORA: hora=HH:MM]
   - Nota: A hora deve corresponder a um dos HORÁRIOS DISPONÍVEIS acima. Se o horário não estiver disponível, informe o cliente e sugira outros slots próximos.

4. Ao coletar alguma observação opcional do cliente para o profissional:
   - Tag: [DEFINIR_OBS: obs=Texto da observação]

5. Quando o cliente concordar com o resumo do agendamento (serviço, data e hora) e desejar enviar para aprovação:
   - Resuma os detalhes do agendamento e avise que foi enviado para aprovação.
   - Tag: [SOLICITAR_AGENDAMENTO]

Importante: Nunca invente serviços ou horários que não estejam explícitos nas listas acima.
Assegure-se de que a resposta final contenha a tag correta em uma nova linha no final da mensagem.
"""
