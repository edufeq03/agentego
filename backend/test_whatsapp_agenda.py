import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# Configure app imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import Servico, Disponibilidade, Bloqueio, Agendamento, Empresa, Lead, EstadoAuxiliar
from app.extrator_agenda import (
    buscar_servico_por_nome,
    validar_extracao,
    calcular_hora_fim,
    montar_resumo_agendamento
)
from app.estado_auxiliar import salvar_estado_auxiliar, carregar_estado_auxiliar, limpar_estado_auxiliar
from app.pipeline_cozinha import processar_comando_cozinha

class TestWhatsappAgenda(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.empresa_id = "11111111-2222-3333-4444-555555555555"
        self.empresa = Empresa(
            id=self.empresa_id,
            nome="Espaço Estética",
            nicho="higienizacao",
            evolution_instance="inst_estetica",
            configuracoes=MagicMock()
        )
        self.empresa.configuracoes.config = {
            "modulos_ativos": ["agenda"],
            "agenda": {
                "whatsapp_profissional": "5511988888888",
                "nome_agente": "Rosana"
            }
        }

    def test_buscar_servico_por_nome(self):
        """Valida que a busca de serviço por nome funciona com correspondência parcial."""
        mock_servico = Servico(id="s1", nome="Limpeza de Pele", ativo=True, duracao_min=60)
        self.db.query.return_value.filter.return_value.all.return_value = [mock_servico]

        res = buscar_servico_por_nome(self.db, self.empresa_id, "limpeza")
        self.assertIsNotNone(res)
        self.assertEqual(res.nome, "Limpeza de Pele")

    def test_validar_extracao_completa(self):
        """Valida a validação de extração com todos os campos preenchidos e válidos."""
        mock_servico = Servico(id="s1", nome="Limpeza de Pele", ativo=True, duracao_min=60)
        self.db.query.return_value.filter.return_value.all.return_value = [mock_servico]

        # Mock slots para a data ser considerada disponível
        with patch('app.agenda_service.calcular_slots', return_value=["14:00", "15:00"]):
            dados = {
                "servico": "Limpeza",
                "data": "2026-06-01",
                "hora": "14:00",
                "cliente_nome": "Maria"
            }
            dados_val, faltando = validar_extracao(self.db, dados, self.empresa_id)
            self.assertEqual(len(faltando), 0)
            self.assertEqual(dados_val["servico_id"], "s1")

    def test_validar_extracao_hora_indisponivel(self):
        """Valida que a hora indisponível gera erro correspondente."""
        mock_servico = Servico(id="s1", nome="Limpeza de Pele", ativo=True, duracao_min=60)
        self.db.query.return_value.filter.return_value.all.return_value = [mock_servico]

        # Mock slots sem a hora desejada
        with patch('app.agenda_service.calcular_slots', return_value=["15:00"]):
            dados = {
                "servico": "Limpeza",
                "data": "2026-06-01",
                "hora": "14:00",
                "cliente_nome": "Maria"
            }
            dados_val, faltando = validar_extracao(self.db, dados, self.empresa_id)
            self.assertIn("hora_indisponivel", faltando)

    def test_calcular_hora_fim(self):
        """Valida que o cálculo do horário de término do serviço está correto."""
        self.assertEqual(calcular_hora_fim("14:00", 60), "15:00")
        self.assertEqual(calcular_hora_fim("14:30", 45), "15:15")

    def test_salvar_carregar_estado_auxiliar(self):
        """Valida persistência do estado auxiliar de conversas."""
        mock_estado = EstadoAuxiliar(empresa_id=self.empresa_id, estado_json='{"aguardando": "campo_agenda"}')
        self.db.query.return_value.filter.return_value.first.return_value = mock_estado

        estado = carregar_estado_auxiliar(self.db, self.empresa_id)
        self.assertEqual(estado["aguardando"], "campo_agenda")

    @patch('app.pipeline_cozinha.enviar_whatsapp')
    def test_comando_rapido_confirmacao(self, mock_enviar_wa):
        """Valida que comandos rápidos no formato '[id] confirmar' funcionam síncronos."""
        with patch('app.agenda_service.confirmar_agendamento', return_value=True) as mock_confirm:
            res = processar_comando_cozinha(self.empresa, "123 confirmar", "5511988888888")
            self.assertIn("confirmado com sucesso", res["resposta"])
            mock_confirm.assert_called_with(unittest.mock.ANY, 123)

if __name__ == '__main__':
    unittest.main()
