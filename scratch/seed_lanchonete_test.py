import sys
import os
import uuid
from datetime import datetime

# Adiciona o diretório backend ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.database import SessionLocal, Empresa, PromptTemplate, Cardapio, Configuracao, init_db

def seed_lanchonete():
    print("Inicializando banco de dados (migrações)...")
    init_db()
    
    db = SessionLocal()
    try:
        print("Semeando nicho Lanchonete...")
        
        # 1. Configurar prompt template do especialista de lanchonete
        prompt_lanchonete = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "lanchonete").first()
        if not prompt_lanchonete:
            prompt_lanchonete = PromptTemplate(
                id=uuid.uuid4(),
                nome_nicho="lanchonete",
                nicho="lanchonete",
                prompt_sistema=(
                    "Você é a Rosana, atendente virtual simpática e ágil da Lanchonete Piccolo.\n"
                    "Sua missão é ajudar os clientes a montarem e confirmarem seus pedidos de lanches no WhatsApp de forma acolhedora, eficiente e organizada.\n\n"
                    "=== DIRETRIZES DE FLUXO E ESTADOS ===\n"
                    "O fluxo de atendimento da lanchonete segue etapas rígidas controladas pelo estado atual da conversa. O estado atual é passado no contexto como 'estado_pedido' ('inicio', 'montando', 'confirmando', 'pedido_feito').\n"
                    "Você deve agir estritamente conforme o estado atual:\n\n"
                    "1. ESTADO: 'inicio'\n"
                    "   - Cumprimente o cliente de forma amigável com um sorriso virtual (emojis).\n"
                    "   - Pergunte como ele gostaria de fazer o pedido: 🛵 Delivery (Entrega), 🛍️ Retirada no Balcão ou 🍽️ Consumo na Mesa.\n"
                    "   - Não passe para a escolha de pratos até que o cliente informe o modo de atendimento!\n"
                    "   - Se ele escolher 'Mesa', pergunte qual o número da mesa.\n"
                    "   - Se escolher 'Delivery', solicite o endereço completo de entrega.\n"
                    "   - IMPORTANTE: Assim que o modo for definido, insira a tag técnica [DEFINIR_MODO: modo=valor] (onde valor é 'delivery', 'balcao' ou 'mesa') e, se aplicável, [ATUALIZAR_LEAD: endereco=...] ou [ATUALIZAR_LEAD: mesa=...]. Isso mudará o estado do pedido para 'montando'.\n\n"
                    "2. ESTADO: 'montando'\n"
                    "   - Apresente as categorias do nosso Cardápio de forma organizada e limpa.\n"
                    "   - Anote os itens e as quantidades escolhidas pelo cliente.\n"
                    "   - Confirme sabores, bebidas e acompanhamentos (ex: pontos de carne, se quer gelo e limão).\n"
                    "   - Sempre informe a disponibilidade dos itens antes de adicioná-los.\n"
                    "   - Sempre que o cliente pedir ou adicionar um item, inclua a tag técnica no final da resposta: [ADICIONAR_ITEM: nome=..., quantidade=..., obs=...].\n"
                    "   - Quando o cliente disser que terminou de escolher tudo e quiser fechar a conta/pedido, você deve levá-lo para a confirmação.\n"
                    "   - Escreva o resumo provisório e adicione a tag técnica [SOLICITAR_CONFIRMACAO] para mudar o estado para 'confirmando'.\n\n"
                    "3. ESTADO: 'confirmando'\n"
                    "   - Exiba um resumo detalhado e legível do pedido contendo:\n"
                    "     * Itens selecionados com preços individuais e quantidade\n"
                    "     * Modo de atendimento escolhido\n"
                    "     * Endereço (se delivery) ou número da mesa (se mesa)\n"
                    "     * Taxa de entrega (se delivery, cobrar R$ 5,00 fixo)\n"
                    "     * Valor Total Geral do pedido\n"
                    "   - Pergunte claramente: 'Podemos confirmar o seu pedido?'\n"
                    "   - Se o cliente confirmar, você DEVE anexar a tag técnica na última linha: [CONFIRMAR_PEDIDO]. Isso criará o pedido no banco e mudará o estado para 'pedido_feito'.\n"
                    "   - Se ele quiser alterar algo, remova itens usando [REMOVER_ITEM: nome=...] e volte o estado para 'montando'.\n\n"
                    "4. ESTADO: 'pedido_feito'\n"
                    "   - Diga que o pedido foi enviado com sucesso para a nossa cozinha! 🎉\n"
                    "   - Informe o número do pedido gerado (ex: Pedido #42).\n"
                    "   - Explique que ele receberá avisos automáticos aqui no WhatsApp sobre o preparo e despacho.\n"
                    "   - Fique à disposição para qualquer outra dúvida ou ajuste rápido.\n\n"
                    "=== REGRAS DE OURO ===\n"
                    "- Colete apenas um dado de cada vez (sem bombardear o cliente com formulários).\n"
                    "- NUNCA ofereça produtos que não estejam listados explicitamente no Cardápio abaixo.\n"
                    "- Seja ágil, use emojis adequados e mantenha uma formatação impecável."
                ),
                tom_voz="Acolhedora, ágil e extremamente simpática com emojis.",
                missao="Anotar e organizar pedidos de lanches dos clientes integrando-os diretamente com a cozinha.",
                objetivo="Concluir a montagem do pedido e obter a confirmação explícita do cliente.",
                etapas_funil=["novo", "interessado", "fechado"]
            )
            db.add(prompt_lanchonete)
            db.commit()
            print("PromptTemplate da lanchonete semeado.")
        else:
            print("PromptTemplate da lanchonete já existente.")
            
        # 2. Criar empresa de teste Piccolo Lanches
        empresa_slug = "piccolo-lanches-teste"
        empresa = db.query(Empresa).filter(Empresa.slug == empresa_slug).first()
        if not empresa:
            empresa = Empresa(
                id=uuid.uuid4(),
                nome="Piccolo Lanches Teste",
                slug=empresa_slug,
                telefone_whatsapp="5511999999999", # Simulador
                telefone_proprietario="5511988888888", # Dono
                webhook_token=str(uuid.uuid4()),
                evolution_instance="piccolo_lanches_instance",
                nicho="lanchonete",
                ativo=True
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
            print(f"Empresa '{empresa.nome}' criada com ID: {empresa.id}")
            
            # Criar configuração associada
            config_dict = {
                "nome_empresa": "Piccolo Lanches Teste",
                "nome_agente": "Rosana",
                "identidade": {
                    "cargo": "Atendente Virtual",
                    "missao": "Auxiliar clientes a fazerem seus pedidos de lanches.",
                    "tom_voz": "Simpático e ágil."
                },
                "whatsapp_cozinha": "5511977777777", # Telefone da cozinha
                "taxa_entrega": 5.00
            }
            config = Configuracao(
                id=uuid.uuid4(),
                empresa_id=empresa.id,
                config=config_dict
            )
            db.add(config)
            db.commit()
            print("Configuração da empresa criada.")
        else:
            print(f"Empresa Piccolo Lanches já existe: {empresa.id}")
            
        # 3. Criar Itens do Cardápio para a Empresa Piccolo Lanches
        itens_existentes = db.query(Cardapio).filter(Cardapio.empresa_id == empresa.id).count()
        if itens_existentes == 0:
            itens_cardapio = [
                # Lanches
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Lanches", nome="X-Burguer", descricao="Pão brioche, hambúrguer de blend artesanal 150g, queijo cheddar derretido e maionese da casa.", preco=18.00, disponivel=True, ordem=10),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Lanches", nome="X-Salada", descricao="Pão brioche, hambúrguer 150g, queijo prato, alface crespa, tomate fresco e maionese verde.", preco=20.00, disponivel=True, ordem=20),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Lanches", nome="X-Tudo", descricao="Pão, hambúrguer 150g, queijo, presunto, bacon crocante, ovo, alface, tomate e batata palha.", preco=28.00, disponivel=True, ordem=30),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Lanches", nome="X-Bacon", descricao="Pão brioche, hambúrguer 150g, muito bacon crocante, cheddar e barbecue artesanal.", preco=24.00, disponivel=True, ordem=40),
                
                # Acompanhamentos
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Acompanhamentos", nome="Batata Frita Média", descricao="Batata palito crocante e sequinha com sal e páprica leve.", preco=12.00, disponivel=True, ordem=50),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Acompanhamentos", nome="Batata Frita com Bacon e Cheddar", descricao="Porção generosa de fritas cobertas com molho cheddar cremoso e farofa de bacon.", preco=22.00, disponivel=True, ordem=60),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Acompanhamentos", nome="Anéis de Cebola", descricao="Anéis de cebola empanados super crocantes (10 unidades).", preco=14.00, disponivel=True, ordem=70),
                
                # Bebidas
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Bebidas", nome="Coca-Cola Lata", descricao="Refrigerante lata 350ml trincando de gelada.", preco=6.00, disponivel=True, ordem=80),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Bebidas", nome="Guaraná Antarctica Lata", descricao="Refrigerante lata 350ml gelada.", preco=6.00, disponivel=True, ordem=90),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Bebidas", nome="Suco de Laranja 500ml", descricao="Suco de laranja natural e espremido na hora.", preco=9.50, disponivel=True, ordem=100),
                Cardapio(id=uuid.uuid4(), empresa_id=empresa.id, categoria="Bebidas", nome="Água Sem Gás", descricao="Garrafa de água mineral 500ml.", preco=4.00, disponivel=True, ordem=110)
            ]
            for item in itens_cardapio:
                db.add(item)
            db.commit()
            print(f"Semeado {len(itens_cardapio)} itens no Cardápio da Piccolo Lanches.")
        else:
            print(f"Cardápio da Piccolo Lanches já possui {itens_existentes} itens.")
            
        print("Seed da Lanchonete concluído com absoluto sucesso!")
    except Exception as e:
        db.rollback()
        print(f"Erro no seed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_lanchonete()
