"""add_followup_delays

Revision ID: a1b2c3d4e5f6
Revises: 3001932720d6
Create Date: 2024-04-29 17:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3001932720d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('campaigns', sa.Column('followup_delay_1', sa.Integer(), nullable=False, server_default='7'))
    op.add_column('campaigns', sa.Column('followup_delay_2', sa.Integer(), nullable=False, server_default='14'))
    op.add_column('campaigns', sa.Column('followup_delay_3', sa.Integer(), nullable=False, server_default='21'))

    op.add_column('campaign_contacts', sa.Column('custom_followup_delay_1', sa.Integer(), nullable=True))
    op.add_column('campaign_contacts', sa.Column('custom_followup_delay_2', sa.Integer(), nullable=True))
    op.add_column('campaign_contacts', sa.Column('custom_followup_delay_3', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('campaigns', 'followup_delay_1')
    op.drop_column('campaigns', 'followup_delay_2')
    op.drop_column('campaigns', 'followup_delay_3')

    op.drop_column('campaign_contacts', 'custom_followup_delay_1')
    op.drop_column('campaign_contacts', 'custom_followup_delay_2')
    op.drop_column('campaign_contacts', 'custom_followup_delay_3')