import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import Servico, Disponibilidade, Bloqueio, Agendamento, Empresa, Lead, ListaEspera, ItemAgendamento
from app.agenda_service import (
    obter_duracao_preco_servico,
    obter_servicos_resolvidos,
    calcular_slots,
    criar_agendamento,
    cancelar_agendamento
)

class TestBelezaNiche(unittest.TestCase):

    def test_obter_duracao_preco_servico_no_override(self):
        """Valida que o serviço retorna a duração e preço padrão quando não há override ou característica."""
        mock_db = MagicMock()
        servico = Servico(
            id=uuid.uuid4(),
            nome="Corte",
            duracao_min=45,
            preco=100.0,
            tem_variacao_caracteristica=True,
            caracteristicas={
                "curto": {"duracao": 30, "preco": 80.0},
                "longo": {"duracao": 60, "preco": 120.0}
            }
        )
        mock_empresa = Empresa(id="emp_id", configuracoes=MagicMock(config={}))
        
        def mock_query(model):
            q = MagicMock()
            if model == Servico:
                q.filter.return_value.first.return_value = servico
            elif model == Empresa:
                q.filter.return_value.first.return_value = mock_empresa
            return q

        mock_db.query.side_effect = mock_query
        
        dur, preco = obter_duracao_preco_servico(mock_db, "emp_id", servico.id, None)
        self.assertEqual(dur, 45)
        self.assertEqual(preco, 100.0)

    def test_obter_duracao_preco_servico_with_override(self):
        """Valida que o serviço retorna a duração e preço da característica se houver override cadastrado."""
        mock_db = MagicMock()
        servico = Servico(
            id=uuid.uuid4(),
            nome="Corte",
            duracao_min=45,
            preco=100.0,
            tem_variacao_caracteristica=True,
            caracteristicas={
                "curto": {"duracao": 30, "preco": 80.0},
                "longo": {"duracao": 60, "preco": 120.0}
            }
        )
        mock_empresa = Empresa(id="emp_id", configuracoes=MagicMock(config={}))
        
        def mock_query(model):
            q = MagicMock()
            if model == Servico:
                q.filter.return_value.first.return_value = servico
            elif model == Empresa:
                q.filter.return_value.first.return_value = mock_empresa
            return q

        mock_db.query.side_effect = mock_query
        
        # Test curto
        dur, preco = obter_duracao_preco_servico(mock_db, "emp_id", servico.id, "curto")
        self.assertEqual(dur, 30)
        self.assertEqual(preco, 80.0)
        
        # Test longo
        dur, preco = obter_duracao_preco_servico(mock_db, "emp_id", servico.id, "longo")
        self.assertEqual(dur, 60)
        self.assertEqual(preco, 120.0)

    def test_obter_servicos_resolvidos_single_and_multi(self):
        """Valida que obter_servicos_resolvidos funciona com ID único ou IDs separados por vírgula."""
        mock_db = MagicMock()
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        
        s1 = Servico(id=id1, nome="Corte", duracao_min=30, preco=50.0, ativo=True)
        s2 = Servico(id=id2, nome="Escova", duracao_min=20, preco=40.0, ativo=True)
        mock_empresa = Empresa(id="emp_id", configuracoes=MagicMock(config={}))
        
        q_servico = MagicMock()
        q_servico.filter.return_value.first.side_effect = [s1, s2]
        
        def mock_query(model):
            if model == Servico:
                return q_servico
            elif model == Empresa:
                q_emp = MagicMock()
                q_emp.filter.return_value.first.return_value = mock_empresa
                return q_emp
            return MagicMock()

        mock_db.query.side_effect = mock_query

        # Multi IDs
        servicos = obter_servicos_resolvidos(mock_db, "emp_id", f"{id1},{id2}")
        self.assertEqual(len(servicos), 2)
        self.assertEqual(servicos[0]["nome"], "Corte")
        self.assertEqual(servicos[1]["nome"], "Escova")

    @patch('app.agenda_service.enviar_whatsapp')
    @patch('app.agenda_service.calcular_slots')
    def test_waitlist_notification_on_cancellation(self, mock_calc_slots, mock_enviar_wa):
        """Valida que o cancelamento de um agendamento notifica o primeiro cliente da lista de espera."""
        mock_db = MagicMock()
        mock_calc_slots.return_value = ["14:00"]
        
        mock_lead = Lead(id="l1", nome="Ana", telefone="5511999990001")
        mock_empresa = Empresa(
            id="emp1", 
            nome="Studio Elegance", 
            evolution_instance="inst1",
            configuracoes=MagicMock(config={"features": {"lista_espera": True}})
        )
        mock_agendamento = Agendamento(
            id=10,
            empresa_id="emp1",
            lead_id="l1",
            servico_id="s1",
            servico_nome="Corte",
            data="2026-06-10",
            hora_inicio="14:00",
            hora_fim="15:00",
            status="confirmado"
        )
        
        # Waitlist item
        waitlist_lead = Lead(id="l2", nome="Bia", telefone="5511999990002", dados_customizados={})
        mock_servico = Servico(id="s1", nome="Corte")
        waitlist_item = ListaEspera(
            id=5,
            empresa_id="emp1",
            lead_id="l2",
            servico_id="s1",
            data="2026-06-10",
            status="aguardando",
            posicao=1,
            lead=waitlist_lead,
            servico=mock_servico
        )
        
        # Mock database queries
        def mock_query(model):
            q = MagicMock()
            if model == Agendamento:
                q.filter.return_value.first.return_value = mock_agendamento
            elif model == Lead:
                q.filter.return_value.first.return_value = mock_lead
            elif model == Empresa:
                q.filter.return_value.first.return_value = mock_empresa
            elif model == ListaEspera:
                q.filter.return_value.order_by.return_value.all.return_value = [waitlist_item]
                q.filter.return_value.first.return_value = waitlist_item
            return q
            
        mock_db.query.side_effect = mock_query
        
        # Cancel booking
        res = cancelar_agendamento(mock_db, 10, "Cancelamento do cliente")
        self.assertTrue(res)
        self.assertEqual(mock_agendamento.status, "cancelado")
        
        # O item da lista de espera deve ter sido atualizado para 'notificado'
        self.assertEqual(waitlist_item.status, "notificado")
        self.assertIsNotNone(waitlist_item.notificado_em)
        self.assertEqual(waitlist_lead.dados_customizados.get("agenda_estado"), "aguardando_confirmacao_lista_espera")
        
        # Verifica se o WhatsApp foi enviado para o lead cancelado e para o lead notificado da lista de espera
        self.assertEqual(mock_enviar_wa.call_count, 2)

if __name__ == '__main__':
    unittest.main()
