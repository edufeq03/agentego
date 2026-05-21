import re
import sys
import os
from sqlalchemy.orm import Session

# Garantir que o diretório correto está no python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot-service')))

from app.database import SessionLocal, Empresa, Lead, Campanha, Mensagem, Evento
from app.pipeline import _atribuir_campanha_se_houver
from app.agents.contexto_agent import contexto_agent

def testar_atribuicao_campanha():
    print("\n--- TESTANDO PARSER E ATRIBUIÇÃO DE CAMPANHAS ---")
    db = SessionLocal()
    try:
        # 1. Carregar ou criar uma empresa de teste
        empresa = db.query(Empresa).first()
        if not empresa:
            print("[ERRO] Nenhuma empresa cadastrada no banco de dados para rodar o teste.")
            return

        # 2. Registrar uma campanha teste para esta empresa
        codigo_teste = "FB-TESTE-123"
        campanha = db.query(Campanha).filter(Campanha.codigo_ref == codigo_teste).first()
        if not campanha:
            campanha = Campanha(
                empresa_id=empresa.id,
                codigo_ref=codigo_teste,
                nome="Campanha de Teste Automatizado",
                origem="facebook",
                descricao="Foco especial em motos Yamaha Fazer 250"
            )
            db.add(campanha)
            db.commit()
            db.refresh(campanha)
            print(f"[OK] Campanha de teste '{codigo_teste}' cadastrada com sucesso.")
        else:
            print(f"[INFO] Campanha '{codigo_teste}' já existe.")

        # 3. Teste 1: Lead com tag cadastrada
        lead1 = Lead(
            empresa_id=empresa.id,
            telefone="559999999991",
            stage="novo",
            canal_entrada="organico"
        )
        db.add(lead1)
        db.commit()
        db.refresh(lead1)

        msg_com_tag = f"Olá! Tenho interesse em fazer cotação. [REF: {codigo_teste}]"
        _atribuir_campanha_se_houver(db, empresa, lead1, msg_com_tag)

        # Atualiza a referência
        db.refresh(lead1)
        assert lead1.utm_campaign == codigo_teste, f"Esperado utm_campaign {codigo_teste}, obtido {lead1.utm_campaign}"
        assert lead1.utm_source == "facebook", f"Esperado utm_source facebook, obtido {lead1.utm_source}"
        assert lead1.canal_entrada == "facebook", f"Esperado canal_entrada facebook, obtido {lead1.canal_entrada}"
        print("[OK] Teste 1: Atribuição de campanha pré-cadastrada funcionou perfeitamente!")

        # 3.5 Teste 1.5: Contexto da Campanha (Nome e Descrição)
        ctx1 = contexto_agent.montar(
            empresa=empresa,
            lead=lead1,
            lead_seguro=None,
            triagem={"intencao": "cotar"},
            config={}
        )
        assert ctx1["campanha"]["nome"] == "Campanha de Teste Automatizado", f"Esperado nome Campanha de Teste Automatizado, obtido {ctx1['campanha']['nome']}"
        assert ctx1["campanha"]["descricao"] == "Foco especial em motos Yamaha Fazer 250", f"Esperado descricao Foco especial em motos Yamaha Fazer 250, obtido {ctx1['campanha']['descricao']}"
        print("[OK] Teste 1.5: Enriquecimento do Contexto com Nome e Descrição da Campanha funcionou com sucesso!")

        # 4. Teste 2: Lead com tag NÃO cadastrada (Fallback)
        lead2 = Lead(
            empresa_id=empresa.id,
            telefone="559999999992",
            stage="novo",
            canal_entrada="organico"
        )
        db.add(lead2)
        db.commit()
        db.refresh(lead2)

        tag_inexistente = "INSTA-PROMO-XYZ"
        msg_inexistente = f"Quero saber mais sobre seguro. [REF: {tag_inexistente}]"
        _atribuir_campanha_se_houver(db, empresa, lead2, msg_inexistente)

        db.refresh(lead2)
        assert lead2.utm_campaign == tag_inexistente, f"Esperado utm_campaign {tag_inexistente}, obtido {lead2.utm_campaign}"
        assert lead2.canal_entrada == "ads_generico", f"Esperado canal_entrada ads_generico, obtido {lead2.canal_entrada}"
        print("[OK] Teste 2: Fallback para campanha não cadastrada (ads_generico) funcionou com sucesso!")

        # Limpar registros temporários
        # Deletar eventos criados para evitar Foreign Key Violations
        db.query(Evento).filter(Evento.lead_id.in_([lead1.id, lead2.id])).delete(synchronize_session=False)
        db.commit()
        
        db.delete(lead1)
        db.delete(lead2)
        db.delete(campanha)
        db.commit()
        print("[INFO] Limpeza de dados de teste concluída.")

    finally:
        db.close()


def testar_contexto_recorrencia():
    print("\n--- TESTANDO MENSAGENS E FLAG DE RECORRÊNCIA ---")
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).first()
        if not empresa:
            print("[ERRO] Nenhuma empresa cadastrada no banco de dados para rodar o teste.")
            return

        # 1. Criar lead teste
        lead = Lead(
            empresa_id=empresa.id,
            telefone="559999999993",
            stage="novo"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        # 2. Testar contexto para lead novo (sem mensagens do agente na conversa)
        ctx_novo = contexto_agent.montar(
            empresa=empresa,
            lead=lead,
            lead_seguro=None,
            triagem={"intencao": "cotar"},
            config={}
        )
        assert ctx_novo["lead_recorrente"] is False, "Esperado lead_recorrente False para lead novo."
        print("[OK] Teste 3: Lead novo corretamente classificado como NÃO recorrente (lead_recorrente = False).")

        # 3. Adicionar mensagens simuladas no histórico
        msg_cliente = Mensagem(
            lead_id=lead.id,
            empresa_id=empresa.id,
            mensagem="Oi",
            tipo="cliente"
        )
        msg_agente = Mensagem(
            lead_id=lead.id,
            empresa_id=empresa.id,
            mensagem="Olá! Eu sou Alice, sua assistente virtual. Como posso ajudar?",
            tipo="agente"
        )
        db.add(msg_cliente)
        db.add(msg_agente)
        db.commit()

        # 4. Testar contexto para lead recorrente (agora com mensagens do agente)
        ctx_recorrente = contexto_agent.montar(
            empresa=empresa,
            lead=lead,
            lead_seguro=None,
            triagem={"intencao": "cotar"},
            config={}
        )
        assert ctx_recorrente["lead_recorrente"] is True, "Esperado lead_recorrente True para lead recorrente."
        print("[OK] Teste 4: Lead antigo corretamente classificado como recorrente (lead_recorrente = True).")

        # Limpar registros temporários
        db.delete(msg_cliente)
        db.delete(msg_agente)
        db.delete(lead)
        db.commit()
        print("[INFO] Limpeza de dados de teste de recorrência concluída.")

    finally:
        db.close()


if __name__ == "__main__":
    try:
        testar_atribuicao_campanha()
        testar_contexto_recorrencia()
        print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
    except AssertionError as e:
        print(f"\n❌ FALHA NA ASSERÇÃO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        sys.exit(1)
