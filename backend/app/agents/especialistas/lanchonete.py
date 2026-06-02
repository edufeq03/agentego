from app.agents.base_agent import BaseAgent
from app.openai_client import perguntar

class EspecialistaLanchonete(BaseAgent):
    nome = "EspecialistaLanchonete"

    def processar(self, mensagem: str, contexto: dict, historico: list) -> tuple[str, int, int]:
        prompt = self._montar_prompt(contexto)
        openai_hist = self.montar_historico_openai(historico)
        
        # Instrução de tags de reforço
        lembrete = (
            "\n\n[INSTRUÇÃO DO SISTEMA: Lembre-se de sempre anexar as tags corretas de acordo com a ação "
            "(ex: [DEFINIR_MODO: modo=...], [ADICIONAR_ITEM: nome=..., quantidade=..., obs=...], [REMOVER_ITEM: nome=...], [SOLICITAR_CONFIRMACAO], [CONFIRMAR_PEDIDO] ou [SALVAR_AVALIACAO: nota=..., comentario=...]) no final da sua resposta!]"
        )
        mensagem_com_lembrete = mensagem + lembrete
        temperature = contexto.get("config", {}).get("openai_temperature", 0.2)
        return perguntar(mensagem_com_lembrete, prompt, openai_hist, temperature=temperature)

    def _montar_prompt(self, ctx: dict) -> str:
        config = ctx["config"]
        nome_agente = ctx["nome_agente"]
        nome_empresa = ctx["nome_empresa"]
        
        # Obter estado do pedido
        dados_pedido = ctx.get("dados_pedido", {})
        estado_pedido = dados_pedido.get("estado", "inicio")
        modo_pedido = dados_pedido.get("modo", "Não definido")
        mesa_pedido = dados_pedido.get("mesa")
        endereco_pedido = dados_pedido.get("endereco")
        nome_balcao_pedido = dados_pedido.get("nome_balcao")
        itens_selecionados = dados_pedido.get("itens", [])
        
        # Carregar Cardápio do banco
        cardapio_str = ctx.get("cardapio_formatado", "Nenhum item cadastrado no cardápio.")
        
        # Formatar itens já selecionados no carrinho
        carrinho_str = "Seu carrinho está vazio."
        if itens_selecionados:
            carrinho_list = []
            for it in itens_selecionados:
                obs = f" (Obs: {it['obs']})" if it.get("obs") else ""
                carrinho_list.append(f"- {it['quantidade']}x {it['nome']} (R$ {it['preco_unit']:.2f} cada){obs}")
            carrinho_str = "\n".join(carrinho_list)
            
        # Obter instruções base da lanchonete (ou usar a padrão cadastrada)
        prompt_sistema = config.get("prompt_sistema") or ""
        
        regras_extras = []
        if config.get("apenas_delivery"):
            regras_extras.append("🚨 ATENÇÃO: A lanchonete está operando APENAS COM DELIVERY no momento. Não ofereça e não aceite opções de comer na mesa ou retirar no balcão.")
        if config.get("exigir_endereco_texto"):
            regras_extras.append("🚨 ATENÇÃO: Para o endereço de entrega, EXIJA RIGOROSAMENTE que o cliente DIGITE o endereço em texto (para evitarmos erros de transcrição de áudio). Se o cliente não digitou claramente o endereço completo, peça para ele escrever.")
            
        regras_extras_str = "\n".join(regras_extras)
        
        return f"""Você é {nome_agente}, assistente virtual de atendimento da {nome_empresa}.
Seu objetivo é guiar o cliente amigavelmente na escolha dos itens e confirmação de pedidos.

=== CARDÁPIO DA CASA ===
{cardapio_str}

=== ESTADO ATUAL DO PEDIDO ===
Estado Atual da Conversa: '{estado_pedido}' (valores possíveis: 'inicio', 'montando', 'confirmando', 'pedido_feito')
Modo Escolhido: {modo_pedido.upper()}
Mesa: {mesa_pedido or 'Não aplicável'}
Endereço de Entrega: {endereco_pedido or 'Não aplicável'}
Nome para Retirada (Balcão): {nome_balcao_pedido or 'Não aplicável'}

=== ITENS NO CARRINHO (MEMÓRIA DO SISTEMA) ===
{carrinho_str}

=== SUA DIRETRIZ POR ESTADO ===
{prompt_sistema}

{regras_extras_str}

=== INSTRUÇÕES TÉCNICAS (OBRIGATÓRIO) ===
Você controla o estado do pedido através de tags técnicas adicionadas na última linha da sua resposta. Sempre adicione as tags quando houver ações:

1. Ao definir o modo de atendimento (Delivery, Balcão, Mesa):
   - Tag: [DEFINIR_MODO: modo=delivery|balcao|mesa]
   - E se houver endereço: [ATUALIZAR_LEAD: endereco=Endereço Completo]
   - E se houver mesa: [ATUALIZAR_LEAD: mesa=Número]

2. Ao adicionar um item ao carrinho:
   - Tag: [ADICIONAR_ITEM: nome=Nome do Prato, quantidade=Qtd, obs=Observações]
   - Exemplo: [ADICIONAR_ITEM: nome=X-Burguer, quantidade=2, obs=Sem cebola e bem passado]
   - Nota: Valide sempre se o item existe no CARDÁPIO DA CASA acima! Se não existir, avise o cliente simpaticamente.

3. Ao remover um item do carrinho:
   - Tag: [REMOVER_ITEM: nome=Nome do Prato]

4. Quando o cliente disser que terminou de escolher e quer fechar o pedido:
   - Apresente o resumo provisório de itens e o total geral.
   - Para delivery, adicione taxa de entrega fixa de R$ 5,00.
   - Tag: [SOLICITAR_CONFIRMACAO]

5. Quando o cliente confirmar expressamente o resumo do pedido no estado 'confirmando':
   - Tag: [CONFIRMAR_PEDIDO]

6. Avaliação de Pós-Venda: Se o cliente estiver respondendo a uma mensagem de pós-venda dando uma nota para o pedido (ex: de 1 a 5) e/ou um comentário sobre como foi a experiência:
   - Tag: [SALVAR_AVALIACAO: nota=Nota numérica de 1 a 5, comentario=Comentário do cliente]
   - Agradeça a avaliação de forma carinhosa.

Nunca misture o formato das tags. Assegure-se de que a resposta final contenha a tag correta em uma nova linha no final.
"""
