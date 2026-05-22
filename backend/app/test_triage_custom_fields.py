#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import random

# Ensure root app directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_triage_custom_fields")

from app.database import SessionLocal, Empresa, Lead, CampoCustomizado
from app.pipeline import _processar_tags
from app.agents.contexto_agent import contexto_agent

def run_verification_test():
    logger.info("======================================================================")
    logger.info("INICIANDO SUITE DE TESTES AUTOMÁTICOS: TRIAGEM DINÂMICA (SPRINT 6)")
    logger.info("======================================================================")

    db = SessionLocal()
    # Inicia transação explícita que será revertida no final (rollback)
    db.begin()

    try:
        # 1. Carregar ou criar empresa de teste
        empresa = db.query(Empresa).first()
        if not empresa:
            logger.info("Nenhuma empresa encontrada no BD. Criando empresa temporária...")
            empresa = Empresa(
                nome="Academia Fit Teste",
                slug="academia-fit-teste",
                nicho="academia"
            )
            db.add(empresa)
            db.flush()
        else:
            logger.info(f"Empresa ativa de teste carregada: {empresa.nome} (Nicho: {empresa.nicho})")

        # 2. Criar Lead de teste com telefone aleatório para evitar FKs do banco
        telefone_teste = f"55119{random.randint(10000000, 99999999)}"
        
        lead = Lead(
            empresa_id=empresa.id,
            telefone=telefone_teste,
            nome="Carlos Teste Dinamico",
            stage="triagem",
            dados_customizados={}
        )
        db.add(lead)
        db.flush()
        logger.info(f"✔ Lead de teste criado com sucesso. ID: {lead.id}, Telefone: {lead.telefone}")

        # 3. Remover campos customizados antigos do teste para garantir isolamento
        db.query(CampoCustomizado).filter(
            CampoCustomizado.empresa_id == empresa.id,
            CampoCustomizado.chave == "preferencia_treino"
        ).delete()
        db.flush()

        # 4. Cadastrar CampoCustomizado do tipo 'opcao_unica'
        campo_custom = CampoCustomizado(
            empresa_id=empresa.id,
            chave="preferencia_treino",
            label="Preferência de Treino",
            tipo="opcao_unica",
            opcoes=["musculacao", "crossfit", "funcional"],
            obrigatorio=True,
            ordem=10,
            ativo=True
        )
        db.add(campo_custom)
        db.flush()
        logger.info("✔ Campo Customizado 'preferencia_treino' cadastrado com sucesso no banco!")

        # 5. Simular mensagem contendo a tag [ATUALIZAR_LEAD: preferencia_treino=crossfit]
        resposta_raw = "Entendido! Vou registrar que seu treino favorito é o de crossfit. [ATUALIZAR_LEAD: preferencia_treino=crossfit]"
        logger.info(f"Simulando parsing de resposta contendo tag: '{resposta_raw}'")
        
        # Executar parsing de tags da pipeline
        _processar_tags(db, empresa, lead, resposta_raw, lead.telefone)
        db.flush()

        # 6. Validar se o valor 'crossfit' foi inserido na coluna dados_customizados do lead no PostgreSQL
        dados = lead.dados_customizados or {}
        logger.info(f"Dados customizados atuais no lead: {dados}")
        
        assert "preferencia_treino" in dados, "Erro: chave 'preferencia_treino' não encontrada nos dados customizados!"
        assert dados["preferencia_treino"] == "crossfit", f"Erro: valor esperado 'crossfit', obtido '{dados.get('preferencia_treino')}'"
        logger.info("✔ ASSERÇÃO 1: Chave-valor salva com absoluto sucesso no JSONB 'dados_customizados' do lead!")

        # 7. Validar se o montador de contexto (ContextoAgent) gera o prompt da IA discriminando os campos corretamente
        ctx = contexto_agent.montar(
            empresa=empresa,
            lead=lead,
            lead_seguro=None,
            triagem={"intencao": "duvida", "sentimento": "neutro"},
            config={"nome_empresa": empresa.nome, "nome_agente": "Rosana"}
        )
        
        campos_coletados = ctx["triagem_dinamica"]["campos_coletados"]
        campos_pendentes = ctx["triagem_dinamica"]["campos_pendentes"]
        
        logger.info("--- Recorte do Prompt do Contexto Injetado na IA ---")
        logger.info(f"  > CAMPOS COLETADOS:\n{campos_coletados}")
        logger.info(f"  > CAMPOS PENDENTES:\n{campos_pendentes}")
        logger.info("---------------------------------------------------")

        assert "Preferência de Treino: crossfit" in campos_coletados, "Erro: O campo coletado 'preferencia_treino' não está formatado no prompt de DADOS JÁ COLETADOS!"
        assert "Preferência de Treino" not in campos_pendentes, "Erro: O campo 'preferencia_treino' continua aparecendo como pendente (falta coletar)!"
        
        logger.info("✔ ASSERÇÃO 2: Montador de contexto e prompts dividiu perfeitamente o campo como coletado!")

        logger.info("======================================================================")
        logger.info("TODOS OS TESTES PASSARAM COM MÁXIMO SUCESSO (100% OK)!")
        logger.info("======================================================================")

    except Exception as e:
        logger.error("❌ FALHA NA VERIFICAÇÃO AUTOMÁTICA DA TRIAGEM:")
        logger.exception(e)
        sys.exit(1)
    finally:
        # Garantia absoluta de banco limpo: Rollback reverte tudo que fizemos na transação!
        logger.info("Limpando ambiente de testes... Executando ROLLBACK no banco de dados.")
        db.rollback()
        db.close()
        logger.info("Conexão fechada. Banco de dados limpo e íntegro!")

if __name__ == "__main__":
    run_verification_test()
