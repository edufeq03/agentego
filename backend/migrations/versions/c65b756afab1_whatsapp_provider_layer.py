"""whatsapp provider layer

Revision ID: c65b756afab1
Revises: 63eadbb5fb7f
Create Date: 2026-07-02 22:38:16.532539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c65b756afab1'
down_revision: Union[str, Sequence[str], None] = '63eadbb5fb7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('''
        ALTER TABLE empresas ADD COLUMN IF NOT EXISTS config_whatsapp JSONB DEFAULT '{
            "provider": "evolution",
            "rate_limit": {
                "mensagens_por_minuto": 12,
                "delay_atendimento_ms": 1500,
                "delay_notificacao_ms": 2000,
                "delay_campanha_min_ms": 3000,
                "delay_campanha_max_ms": 6000,
                "campanha_limite_por_minuto": 8,
                "campanha_horario_inicio": "08:00",
                "campanha_horario_fim": "20:00"
            }
        }'
    ''')
    
    op.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_send_log (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            campanha_id     UUID REFERENCES campanhas(id) ON DELETE SET NULL,
            telefone        VARCHAR(30) NOT NULL,
            tipo            VARCHAR(20) NOT NULL,
            contexto        VARCHAR(20) NOT NULL,
            provider        VARCHAR(20) NOT NULL,
            sucesso         BOOLEAN NOT NULL,
            message_id      VARCHAR(200),
            erro            TEXT,
            delay_aplicado_ms INTEGER,
            enviado_em      TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    op.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_send_log_tenant ON whatsapp_send_log (tenant_id, enviado_em)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_send_log_campanha ON whatsapp_send_log (campanha_id)')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP TABLE IF EXISTS whatsapp_send_log')
    op.execute('ALTER TABLE empresas DROP COLUMN IF EXISTS config_whatsapp')
