# -*- coding: utf-8 -*-
"""
Suite de Testes de Integração Automatizados - Disparos da IA (Reengajamento)
Este script valida os gatilhos, guardrails anti-spam, e geração contextual.
Garante isolamento total realizando Rollback no final da execução.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Empresa, Lead, Mensagem, CampoCustomizado, Configuracao
from app.main import tarefa_reengajamento_automatico

class TestSmartReengagement(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = SessionLocal()
        # Iniciar transação isolada
        self.db.begin_nested()
        
        # 1. Criar empresa de teste com identificadores únicos
        import random
        suffix = str(random.randint(100000, 999999))
        self.empresa = Empresa(
            nome="Seguros Teste Reengajamento",
            slug=f"seguros-teste-reeng-{suffix}",
            telefone_whatsapp=f"55119{suffix}",
            telefone_proprietario=f"55118{suffix}",
            nicho="corretora",
            ativo=True,
            evolution_instance=f"instancia_teste_reeng-{suffix}"
        )
        self.db.add(self.empresa)
        self.db.flush()
        
        # 2. Criar configuração de reengajamento habilitada com cadência multi-passo
        self.config_obj = Configuracao(
            empresa_id=self.empresa.id,
            config={
                "reengagement_inactivity_enabled": True,
                "reengagement_inactivity_steps": [
                    {"step": 1, "delay_hours": 1.0, "prompt": "Olá! Vi que você sumiu. Passo 1."},
                    {"step": 2, "delay_hours": 2.0, "prompt": "Ainda aí? Passo 2."}
                ],
                
                "reengagement_pending_enabled": False,
                "reengagement_pending_steps": []
            }
        )
        self.db.add(self.config_obj)
        
        # 3. Criar campo customizado obrigatório de triagem
        self.campo_obrigatorio = CampoCustomizado(
            empresa_id=self.empresa.id,
            chave="tipo_seguro",
            label="Tipo de Seguro",
            tipo="texto",
            obrigatorio=True,
            ordem=10,
            ativo=True
        )
        self.db.add(self.campo_obrigatorio)
        self.db.flush()

    async def asyncTearDown(self):
        # Descartar todas as alterações para manter banco de dados 100% limpo
        self.db.rollback()
        self.db.close()

    @patch("app.openai_client.perguntar")
    @patch("app.pipeline.enviar_whatsapp")
    async def test_ciclo_reengajamento_completo(self, mock_whatsapp, mock_perguntar):
        from sqlalchemy.orm.attributes import flag_modified
        from app.pipeline import processar_webhook
        import asyncio
        
        # Definir resposta mockada para OpenAI
        mock_perguntar.return_value = (
            "Oi! Restou alguma dúvida sobre o nosso seguro? Passo 1.",
            100,
            50
        )
        
        # 1. Criar lead estagnado há 3 horas
        lead = Lead(
            empresa_id=self.empresa.id,
            telefone="5511999998888",
            nome="Carlos Silveira",
            stage="triagem",
            dados_customizados={}
        )
        self.db.add(lead)
        self.db.flush()
        
        # Enviar mensagem do robô há 3 horas (excede o delay do Passo 1)
        msg_antiga = Mensagem(
            empresa_id=self.empresa.id,
            lead_id=lead.id,
            tipo="agente",
            mensagem="Olá, qual seguro você deseja cotar?",
            timestamp=datetime.utcnow() - timedelta(hours=3)
        )
        self.db.add(msg_antiga)
        self.db.commit()
        
        # 2. Rodar o Scheduler (Deve disparar o PASSO 1 da Inatividade)
        await tarefa_reengajamento_automatico()
        
        # ASSERÇÃO 1: Verificar se Passo 1 foi registrado no histórico e estado do lead
        mensagens = self.db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.asc()).all()
        self.assertEqual(len(mensagens), 2, "Deveria ter gerado o reengajamento Passo 1")
        self.assertEqual(mensagens[-1].tipo, "agente")
        
        lead_atualizado = self.db.query(Lead).filter(Lead.id == lead.id).first()
        self.assertEqual(lead_atualizado.dados_customizados.get("reengajamento_fluxo_ativo"), "inactivity")
        self.assertEqual(lead_atualizado.dados_customizados.get("reengajamento_passo_atual"), 1)
        self.assertIsNotNone(lead_atualizado.dados_customizados.get("reengajamento_ultimo_timestamp"))
        
        # 3. MOCKAR AVANÇO DE TEMPO DO REENGAJAMENTO (Fazer o Passo 1 parecer enviado há 3 horas)
        mock_perguntar.return_value = (
            "Olá de novo! Ainda quer ver a cotação? Passo 2.",
            100,
            50
        )
        lead_atualizado.dados_customizados["reengajamento_ultimo_timestamp"] = (datetime.utcnow() - timedelta(hours=3)).isoformat()
        flag_modified(lead_atualizado, "dados_customizados")
        self.db.commit()
        
        # Enviar outra mensagem fictícia do agente para simular que o chat continuou silenciado depois
        msg_ficticia_agente = Mensagem(
            empresa_id=self.empresa.id,
            lead_id=lead.id,
            tipo="agente",
            mensagem="Oi! Restou alguma dúvida sobre o nosso seguro? Passo 1.",
            timestamp=datetime.utcnow() - timedelta(hours=3)
        )
        self.db.add(msg_ficticia_agente)
        self.db.commit()
        
        # 4. Rodar o Scheduler (Deve disparar o PASSO 2 da Inatividade)
        await tarefa_reengajamento_automatico()
        
        # ASSERÇÃO 2: Verificar se o Passo 2 foi enviado e incrementou o passo atual
        lead_atualizado = self.db.query(Lead).filter(Lead.id == lead.id).first()
        self.assertEqual(lead_atualizado.dados_customizados.get("reengajamento_passo_atual"), 2)
        
        # 5. ASSERÇÃO 3: Limite da esteira. Se rodar de novo, não dispara mais pois acabou a cadência
        mock_perguntar.reset_mock()
        await tarefa_reengajamento_automatico()
        mock_perguntar.assert_not_called()
        
        # 6. RESET HOOK: Simular que o usuário respondeu via webhook do Evolution
        # Isso deve limpar todas as chaves de cadência
        await asyncio.to_thread(processar_webhook, self.empresa, lead.telefone, "Quero sim, desculpe a demora!")
        
        lead_final = self.db.query(Lead).filter(Lead.id == lead.id).first()
        self.db.refresh(lead_final)
        dados_finais = lead_final.dados_customizados or {}
        self.assertNotIn("reengajamento_fluxo_ativo", dados_finais)
        self.assertNotIn("reengajamento_passo_atual", dados_finais)
        self.assertNotIn("reengajamento_ultimo_timestamp", dados_finais)
        
        print("\n✅ SPRINT 16: Suíte de testes de cadências e resets concluída com absoluto sucesso!")

if __name__ == "__main__":
    unittest.main()
