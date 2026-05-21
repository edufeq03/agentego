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
            evolution_instance="instancia_teste_reeng"
        )
        self.db.add(self.empresa)
        self.db.flush()
        
        # 2. Criar configuração de reengajamento habilitada
        self.config_obj = Configuracao(
            empresa_id=self.empresa.id,
            config={
                "reengagement_inactivity_enabled": True,
                "reengagement_inactivity_delay_hours": 2,
                "reengagement_inactivity_prompt": "Olá! Gostaria de saber se ficou com alguma dúvida sobre nossos seguros.",
                
                "reengagement_pending_enabled": True,
                "reengagement_pending_delay_hours": 1,
                "reengagement_pending_prompt": "Lembre o lead de que precisamos das informações pendentes ({campos_pendentes}) para prosseguir."
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
        # Definir resposta mockada para OpenAI
        mock_perguntar.return_value = (
            "Olá! Notamos que faltou preencher o Tipo de Seguro para prosseguir com sua cotação. Vamos finalizar?",
            100,
            50
        )
        
        # 1. Criar lead estagnado há 3 horas
        lead = Lead(
            empresa_id=self.empresa.id,
            telefone="5511999998888",
            nome="Carlos Silveira",
            stage="triagem",
            dados_customizados={} # Nenhuma informação preenchida (tipo_seguro está pendente!)
        )
        self.db.add(lead)
        self.db.flush()
        
        # Enviar mensagem do robô há 3 horas (excede o delay de 1h pendente e 2h inatividade)
        msg_antiga = Mensagem(
            empresa_id=self.empresa.id,
            lead_id=lead.id,
            tipo="agente",
            mensagem="Olá, qual seguro você deseja cotar?",
            timestamp=datetime.utcnow() - timedelta(hours=3)
        )
        self.db.add(msg_antiga)
        self.db.commit()
        
        # 2. Rodar a tarefa em background do Scheduler
        # Como ela é async, podemos chamá-la diretamente
        await tarefa_reengajamento_automatico()
        
        # 3. ASSERÇÃO: Verificar se uma nova mensagem do robô foi gerada e registrada
        mensagens = self.db.query(Mensagem).filter(Mensagem.lead_id == lead.id).order_by(Mensagem.timestamp.asc()).all()
        self.assertEqual(len(mensagens), 2, "Deveria ter gerado o reengajamento e somado 2 mensagens no histórico")
        
        reeng_msg = mensagens[-1]
        self.assertEqual(reeng_msg.tipo, "agente")
        self.assertIn("notamos que faltou preencher", reeng_msg.mensagem.lower())
        
        # 4. ASSERÇÃO: Verificar se o timestamp de controle foi inserido para evitar spam
        lead_atualizado = self.db.query(Lead).filter(Lead.id == lead.id).first()
        self.assertIsNotNone(lead_atualizado.dados_customizados.get("ultimo_reengajamento_pendente"))
        self.assertEqual(lead_atualizado.dados_customizados["ultimo_reengajamento_pendente"], msg_antiga.timestamp.isoformat())
        
        # 5. ASSERÇÃO: Rodar o motor de reengajamento novamente e verificar que NÃO envia duplicado (Guardrail Anti-Spam!)
        mock_perguntar.reset_mock()
        await tarefa_reengajamento_automatico()
        mock_perguntar.assert_not_called()
        
        # Garantir que continuam apenas 2 mensagens no histórico
        mensagens_depois = self.db.query(Mensagem).filter(Mensagem.lead_id == lead.id).all()
        self.assertEqual(len(mensagens_depois), 2, "Guardrail anti-spam falhou e duplicou o envio!")
        
        print("\n\u2705 SPRINT 11: Todos os testes de integração do Reengajamento Inteligente passaram com sucesso!")

if __name__ == "__main__":
    unittest.main()

