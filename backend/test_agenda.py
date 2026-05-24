import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
import pytz

# Configure app imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import Servico, Disponibilidade, Bloqueio, Agendamento, Empresa, Lead
from app.agenda_service import (
    hm_to_min,
    min_to_hm,
    calcular_slots,
    criar_agendamento_cliente,
    confirmar_agendamento,
    recusar_agendamento,
    cancelar_agendamento,
    tarefa_processar_agenda
)
from app.parser_data import parse_data, parse_hora

class TestAgendaModule(unittest.TestCase):

    def test_time_conversions(self):
        """Valida conversão de HH:MM para minutos e vice-versa."""
        self.assertEqual(hm_to_min("08:00"), 480)
        self.assertEqual(hm_to_min("14:30"), 870)
        self.assertEqual(hm_to_min("00:00"), 0)
        
        self.assertEqual(min_to_hm(480), "08:00")
        self.assertEqual(min_to_hm(870), "14:30")
        self.assertEqual(min_to_hm(0), "00:00")

    def test_parser_data_pt_br(self):
        """Valida que o parser de data em português lida com termos relativos e absolutos."""
        agora = datetime.now()
        
        # Teste "amanhã"
        amanha = agora + timedelta(days=1)
        parsed_amanha = parse_data("amanhã")
        self.assertIsNotNone(parsed_amanha)
        self.assertEqual(parsed_amanha, amanha.date())
        
        # Teste "hoje"
        parsed_hoje = parse_data("hoje")
        self.assertIsNotNone(parsed_hoje)
        self.assertEqual(parsed_hoje, agora.date())

        # Teste "segunda" (próxima segunda-feira)
        parsed_segunda = parse_data("segunda-feira")
        self.assertIsNotNone(parsed_segunda)
        
        # Teste hora
        self.assertEqual(parse_hora("às 2 da tarde"), "14:00")
        self.assertEqual(parse_hora("8 da noite"), "20:00")
        self.assertEqual(parse_hora("10:30"), "10:30")
        self.assertEqual(parse_hora("meio dia"), "12:00")

    @patch('app.agenda_service.enviar_whatsapp')
    def test_confirmar_recusar_cancelar_agendamento(self, mock_enviar_wa):
        """Valida fluxos de atualização de status (confirmar, recusar, cancelar)."""
        mock_db = MagicMock()
        
        mock_lead = Lead(id="111", nome="Bruno", telefone="5511999999999", stage="coletando_dados")
        mock_empresa = Empresa(id="222", nome="Consultorio", evolution_instance="inst_1")
        mock_agendamento = Agendamento(
            id=123,
            empresa_id="222",
            lead_id="111",
            servico_nome="Consulta",
            data="2026-06-01",
            hora_inicio="14:00",
            hora_fim="14:30",
            status="pendente"
        )
        
        # Configure mock_db queries cleanly based on query parameter model
        def mock_query(model):
            q = MagicMock()
            if model == Agendamento:
                q.filter.return_value.first.return_value = mock_agendamento
            elif model == Lead:
                q.filter.return_value.first.return_value = mock_lead
            elif model == Empresa:
                q.filter.return_value.first.return_value = mock_empresa
            return q
            
        mock_db.query.side_effect = mock_query
        
        # Confirmar
        res = confirmar_agendamento(mock_db, 123)
        self.assertTrue(res)
        self.assertEqual(mock_agendamento.status, "confirmado")
        self.assertEqual(mock_lead.stage, "agendado")
        mock_enviar_wa.assert_called_with(
            "5511999999999",
            "✅ *Seu agendamento foi confirmado!*\n\n💼 *Serviço:* Consulta\n📅 *Data:* 01/06/2026\n⏰ *Horário:* 14:00\n\nAguardamos você! Qualquer dúvida, estamos à disposição.",
            "inst_1"
        )

        # Recusar (precisa resetar status para pendente para poder recusar no teste)
        mock_agendamento.status = "pendente"
        res_recusar = recusar_agendamento(mock_db, 123, "Sem vagas")
        self.assertTrue(res_recusar)
        self.assertEqual(mock_agendamento.status, "recusado")
        self.assertEqual(mock_agendamento.motivo_cancelamento, "Sem vagas")
        
        # Cancelar
        mock_agendamento.status = "confirmado"
        res_cancelar = cancelar_agendamento(mock_db, 123, "Cliente pediu")
        self.assertTrue(res_cancelar)
        self.assertEqual(mock_agendamento.status, "cancelado")
        self.assertEqual(mock_agendamento.motivo_cancelamento, "Cliente pediu")

if __name__ == '__main__':
    unittest.main()
