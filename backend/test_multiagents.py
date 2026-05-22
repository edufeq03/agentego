import unittest
from unittest.mock import MagicMock, patch

# Configure app imports
import sys
import os
os.environ["OPENAI_API_KEY"] = "mock-key"
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.agents.base_agent import BaseAgent
from app.agents.triagem_agent import TriagemAgent
from app.agents.contexto_agent import ContextoAgent
from app.agents.especialistas import get_especialista
from app.agents.especialistas.generico import EspecialistaGenerico
from app.agents.especialistas.corretora import EspecialistaCorretora
from app.agents.especialistas.contabilidade import EspecialistaContabilidade
from app.agent import processar_mensagem_dinamica

class TestMultiagents(unittest.TestCase):

    def test_triagem_agent_mocked(self):
        """Valida se o TriagemAgent formata a requisição corretamente e trata respostas JSON."""
        agent = TriagemAgent()
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"intencao": "preco", "sentimento": "positivo", "urgente": false, "resumo_curto": "Consulta de preço"}'))
        ]
        
        with patch('app.agents.triagem_agent.client.chat.completions.create', return_value=mock_response) as mock_create:
            resultado = agent.analisar("Quero saber o preço da mensalidade")
            
            self.assertEqual(resultado["intencao"], "preco")
            self.assertEqual(resultado["sentimento"], "positivo")
            self.assertFalse(resultado["urgente"])
            self.assertEqual(resultado["resumo_curto"], "Consulta de preço")
            mock_create.assert_called_once()

    def test_contexto_agent(self):
        """Valida a injeção limpa de contextos do ContextoAgent."""
        agent = ContextoAgent()
        
        mock_empresa = MagicMock(nome="Piccolo Seguros", nicho="corretora")
        mock_lead = MagicMock(id=1, telefone="5511999999999", stage="coletando_dados", nome="Bruno")
        mock_lead_seguro = MagicMock(
            tipo_seguro="saude",
            nome_segurado="Bruno",
            idade_segurado="30",
            tem_cnpj=True,
            e_mei=False,
            tem_plano_anterior=None,
            plano_anterior_nome=None,
            mais_de_6_meses=None,
            regiao="Campinas",
            hospitais_preferidos="Siriolibanes",
            marca_modelo=None,
            ano_fabricacao=None,
            ano_modelo=None,
            placa=None,
            cep_pernoite=None,
            uso_veiculo=None,
            tem_garagem=None,
            condutor_principal=None,
            idade_condutor=None,
            bonus_classe=None,
            docs_pendentes=["cnh_ou_rg"]
        )
        
        triagem = {
            "intencao": "preco",
            "sentimento": "neutro",
            "urgente": False,
            "resumo_curto": "quer cotar"
        }
        
        config = {
            "nome_agente": "Rosana",
            "nome_empresa": "Piccolo Seguros"
        }
        
        ctx = agent.montar(
            empresa=mock_empresa,
            lead=mock_lead,
            lead_seguro=mock_lead_seguro,
            triagem=triagem,
            config=config
        )
        
        self.assertEqual(ctx["nome_agente"], "Rosana")
        self.assertEqual(ctx["nome_empresa"], "Piccolo Seguros")
        self.assertEqual(ctx["nicho"], "corretora")
        self.assertEqual(ctx["intencao"], "preco")
        self.assertIn("Nome do Segurado: Bruno", ctx["dados_lead_seguro"])
        self.assertIn("Tem CNPJ: Sim", ctx["dados_lead_seguro"])
        self.assertIn("cnh_ou_rg", ctx["docs_pendentes"])

    def test_factory_especialista(self):
        """Valida que get_especialista retorna o agente de domínio correto."""
        self.assertIsInstance(get_especialista("corretora"), EspecialistaCorretora)
        self.assertIsInstance(get_especialista("contabilidade"), EspecialistaContabilidade)
        self.assertIsInstance(get_especialista("academia"), EspecialistaGenerico)
        self.assertIsInstance(get_especialista("nicho_inexistente"), EspecialistaGenerico)

    @patch('app.agents.especialistas.generico.perguntar', return_value=("Olá! Como posso te ajudar?", 100, 50))
    def test_processar_mensagem_dinamica_compatibilidade(self, mock_perguntar):
        """Valida compatibilidade do adaptador legado processar_mensagem_dinamica."""
        config = {
            "nome_agente": "Rosana",
            "nome_empresa": "Corretora Piccolo",
            "nicho": "generico"
        }
        
        resposta, t_in, t_out = processar_mensagem_dinamica(
            mensagem_usuario="Quero cotar plano de saude",
            config=config,
            intencao="preco",
            stage="novo",
            contexto_tempo="Dia de hoje: Quinta-feira",
            historico=[]
        )
        
        self.assertEqual(resposta, "Olá! Como posso te ajudar?")
        self.assertEqual(t_in, 100)
        self.assertEqual(t_out, 50)
        mock_perguntar.assert_called_once()

    def test_resilient_tag_parser_and_age_calc(self):
        """Valida que o parser de tags no pipeline calcula idade de nascimento/anos e suporta multiplas atribuições."""
        from app.pipeline import _processar_tags
        from datetime import date
        
        mock_db = MagicMock()
        mock_empresa = MagicMock(nicho="corretora")
        mock_lead = MagicMock()
        
        mock_lead_seguro = MagicMock()
        mock_lead_seguro.docs_recebidos = []
        mock_lead_seguro.docs_pendentes = []
        
        mock_db.query().filter().first.return_value = mock_lead_seguro
        
        hoje = date.today()
        expected_age = hoje.year - 1984 - ((hoje.month, hoje.day) < (6, 18))
        
        resposta_raw = f"Ok! [ATUALIZAR_LEAD: idade_segurado=18/06/1984, tem_cnpj=false] [SOLICITAR_HUMANO: motivo=Sucesso]"
        
        with patch('app.pipeline.atualizar_status_transbordo') as mock_transbordo, \
             patch('app.pipeline.enviar_whatsapp') as mock_send_wa:
            
            _processar_tags(mock_db, mock_empresa, mock_lead, resposta_raw, "5511999999999")
            
            self.assertEqual(mock_lead_seguro.idade_segurado, expected_age)
            self.assertEqual(mock_lead_seguro.tem_cnpj, False)
            mock_transbordo.assert_called_once_with(mock_db, mock_empresa.id, "5511999999999", "pausado", lead_id=mock_lead.id)

if __name__ == '__main__':
    unittest.main()
