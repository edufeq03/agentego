import sys
import os
import logging

# Adiciona o diretório backend ao path para importação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

# Configura o logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_flow")

from app.database import SessionLocal, Empresa, Lead, Pedido, ItemPedido, Cardapio
from app.pipeline_lanchonete import processar_pipeline_lanchonete
from app.pipeline_cozinha import processar_comando_cozinha
from app.pedido_service import obter_pedido_por_numero

def run_simulation():
    db = SessionLocal()
    try:
        logger.info("=== INICIANDO SIMULAÇÃO DE VENDAS LANCHONETE (END-TO-END) ===")
        
        # 1. Obter a empresa de teste
        empresa_slug = "piccolo-lanches-teste"
        empresa = db.query(Empresa).filter(Empresa.slug == empresa_slug).first()
        if not empresa:
            logger.error("❌ Empresa de teste não encontrada. Por favor rode a seed primeiro.")
            return
            
        logger.info(f"✅ Empresa encontrada: {empresa.nome} (ID: {empresa.id})")
        
        # 2. Configurar telefone de teste do cliente e limpar estados anteriores
        telefone_cliente = "5511999990000"
        
        logger.info(f"🧹 Limpando dados de testes anteriores para o número {telefone_cliente}...")
        
        # Deletar pedidos e itens associados ao lead antigo
        lead_antigo = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone_cliente).first()
        if lead_antigo:
            pedidos_antigos = db.query(Pedido).filter(Pedido.lead_id == lead_antigo.id).all()
            for ped in pedidos_antigos:
                db.query(ItemPedido).filter(ItemPedido.pedido_id == ped.id).delete()
                db.delete(ped)
            db.delete(lead_antigo)
            db.commit()
            logger.info("✅ Dados de testes antigos limpos com sucesso.")
            
        # 3. PASSO 1: Iniciar Conversa (Estado: inicio)
        logger.info("\n💬 [PASSO 1] Cliente envia: 'Olá, boa noite!'")
        resposta_1 = processar_pipeline_lanchonete(empresa, telefone_cliente, "Olá, boa noite!")
        logger.info(f"🤖 IA respondeu:\n------------------\n{resposta_1['resposta']}\n------------------")
        
        # Verificar se o lead foi criado e está no estado correto
        db.expire_all()
        lead = db.query(Lead).filter(Lead.empresa_id == empresa.id, Lead.telefone == telefone_cliente).first()
        assert lead is not None, "Lead deveria ter sido criado"
        dados_cust = lead.dados_customizados or {}
        logger.info(f"📌 Estado atual do Pedido no BD: '{dados_cust.get('pedido_estado')}'")
        assert dados_cust.get("pedido_estado") == "inicio", "O estado deveria ser 'inicio'"
        
        # 4. PASSO 2: Definir Modo de Atendimento (Delivery) e Endereço
        logger.info("\n💬 [PASSO 2] Cliente envia: 'Quero por Delivery na Rua dos Pinheiros, 123'")
        resposta_2 = processar_pipeline_lanchonete(empresa, telefone_cliente, "Quero por Delivery na Rua dos Pinheiros, 123")
        logger.info(f"🤖 IA respondeu:\n------------------\n{resposta_2['resposta']}\n------------------")
        
        db.refresh(lead)
        dados_cust = lead.dados_customizados or {}
        logger.info(f"📌 Estado atual do Pedido no BD: '{dados_cust.get('pedido_estado')}'")
        logger.info(f"📌 Modo de Atendimento: '{dados_cust.get('pedido_modo')}'")
        logger.info(f"📌 Endereço Salvo: '{dados_cust.get('pedido_endereco')}'")
        assert dados_cust.get("pedido_estado") == "montando", "O estado deveria ter mudado para 'montando'"
        assert dados_cust.get("pedido_modo") == "delivery", "O modo deveria ser 'delivery'"
        assert "rua dos pinheiros" in dados_cust.get("pedido_endereco").lower(), "Endereço deveria ter sido salvo"
        
        # 5. PASSO 3: Adicionar Itens ao Carrinho
        logger.info("\n💬 [PASSO 3] Cliente envia: 'Quero dois X-Tudo, uma Batata Frita Média e uma Coca-Cola'")
        resposta_3 = processar_pipeline_lanchonete(empresa, telefone_cliente, "Quero dois X-Tudo, uma Batata Frita Média e uma Coca-Cola")
        logger.info(f"🤖 IA respondeu:\n------------------\n{resposta_3['resposta']}\n------------------")
        
        db.refresh(lead)
        dados_cust = lead.dados_customizados or {}
        itens_carrinho = dados_cust.get("pedido_itens", [])
        logger.info(f"🛒 Itens no carrinho em memória: {itens_carrinho}")
        assert len(itens_carrinho) >= 3, "Deveriam ter no mínimo 3 itens no carrinho"
        
        # 6. PASSO 4: Solicitar Fechamento/Confirmação
        logger.info("\n💬 [PASSO 4] Cliente envia: 'Pode fechar a conta e confirmar pra mim'")
        resposta_4 = processar_pipeline_lanchonete(empresa, telefone_cliente, "Pode fechar a conta e confirmar pra mim")
        logger.info(f"🤖 IA respondeu:\n------------------\n{resposta_4['resposta']}\n------------------")
        
        db.refresh(lead)
        dados_cust = lead.dados_customizados or {}
        logger.info(f"📌 Estado atual do Pedido no BD: '{dados_cust.get('pedido_estado')}'")
        assert dados_cust.get("pedido_estado") == "confirmando", "O estado deveria ter mudado para 'confirmando'"
        
        # 7. PASSO 5: Confirmar Pedido de Fato
        logger.info("\n💬 [PASSO 5] Cliente envia: 'Sim, está tudo perfeito! Confirmo o pedido.'")
        resposta_5 = processar_pipeline_lanchonete(empresa, telefone_cliente, "Sim, está tudo perfeito! Confirmo o pedido.")
        logger.info(f"🤖 IA respondeu:\n------------------\n{resposta_5['resposta']}\n------------------")
        
        db.refresh(lead)
        dados_cust = lead.dados_customizados or {}
        logger.info(f"📌 Estado final do Pedido no BD: '{dados_cust.get('pedido_estado')}'")
        assert dados_cust.get("pedido_estado") == "pedido_feito", "O estado deveria ser 'pedido_feito'"
        
        # 8. Validar Pedido Criado no Banco de Dados
        pedido_db = db.query(Pedido).filter(Pedido.lead_id == lead.id).order_by(Pedido.criado_em.desc()).first()
        assert pedido_db is not None, "Pedido deveria ter sido criado no BD"
        logger.info(f"🎉 PEDIDO PERSISTIDO COM SUCESSO!")
        logger.info(f"   • Número do Pedido: #{pedido_db.numero_pedido}")
        logger.info(f"   • Status Inicial: {pedido_db.status}")
        logger.info(f"   • Modo de Atendimento: {pedido_db.modo}")
        logger.info(f"   • Total Calculado: R$ {pedido_db.total:.2f}")
        
        # 2x X-Tudo (R$ 28.00 cada) = R$ 56.00
        # 1x Batata Frita Média = R$ 12.00
        # 1x Coca-Cola Lata = R$ 6.00
        # Taxa de entrega = R$ 5.00
        # Total Esperado = 56 + 12 + 6 + 5 = R$ 79.00
        logger.info(f"   • Total Esperado: R$ 79.00")
        assert abs(pedido_db.total - 79.00) < 0.01, f"Preço incorreto! Recebeu {pedido_db.total}, esperado 79.00"
        logger.info("   ✅ CÁLCULO DE VALORES E PERSISTÊNCIA 100% CORRETOS!")
        
        # 9. Testar Comando de Cozinha
        logger.info("\n=============================================")
        logger.info("🍳 SIMULANDO COMANDOS DA COZINHA (FAST REGEX)")
        logger.info("=============================================")
        
        numero_pedido = pedido_db.numero_pedido
        
        # 9.1 Comando: ok
        logger.info(f"💬 [COZINHA] Envia: '{numero_pedido} ok'")
        res_cmd = processar_comando_cozinha(empresa, f"{numero_pedido} ok")
        logger.info(f"🍳 Cozinha respondeu: {res_cmd['resposta']}")
        
        db.refresh(pedido_db)
        logger.info(f"📌 Status do pedido no BD: '{pedido_db.status}'")
        assert pedido_db.status == "em_preparo", "Deveria estar em preparo"
        
        # 9.2 Comando: tempo
        logger.info(f"💬 [COZINHA] Envia: '{numero_pedido} tempo 25'")
        res_cmd = processar_comando_cozinha(empresa, f"{numero_pedido} tempo 25")
        logger.info(f"🍳 Cozinha respondeu: {res_cmd['resposta']}")
        
        # 9.3 Comando: pedidos (Listagem)
        logger.info(f"💬 [COZINHA] Envia: 'pedidos'")
        res_cmd = processar_comando_cozinha(empresa, "pedidos")
        logger.info(f"🍳 Cozinha respondeu:\n------------------\n{res_cmd['resposta']}\n------------------")
        
        # 9.4 Comando: pronto
        logger.info(f"💬 [COZINHA] Envia: '{numero_pedido} pronto'")
        res_cmd = processar_comando_cozinha(empresa, f"{numero_pedido} pronto")
        logger.info(f"🍳 Cozinha respondeu: {res_cmd['resposta']}")
        
        db.refresh(pedido_db)
        logger.info(f"📌 Status do pedido no BD: '{pedido_db.status}'")
        assert pedido_db.status == "pronto", "Deveria estar pronto"
        
        # 9.5 Comando: entregue
        logger.info(f"💬 [COZINHA] Envia: '{numero_pedido} entregue'")
        res_cmd = processar_comando_cozinha(empresa, f"{numero_pedido} entregue")
        logger.info(f"🍳 Cozinha respondeu: {res_cmd['resposta']}")
        
        db.refresh(pedido_db)
        logger.info(f"📌 Status do pedido no BD: '{pedido_db.status}'")
        assert pedido_db.status == "entregue", "Deveria estar entregue"
        
        logger.info("\n🎉 SIMULAÇÃO END-TO-END CONCLUÍDA COM 100% DE SUCESSO!")
        logger.info("TUDO FUNCIONANDO PERFEITAMENTE!")
        
    except Exception as e:
        logger.error(f"❌ Falha crítica na simulação: {e}", exc_info=True)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_simulation()
