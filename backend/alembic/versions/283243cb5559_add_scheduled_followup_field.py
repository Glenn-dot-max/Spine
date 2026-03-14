"""add_scheduled_followup_field

Revision ID: 283243cb5559
Revises: 99bf6cde3203
Create Date: 2026-03-14 12:10:01.030563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '283243cb5559'
down_revision: Union[str, Sequence[str], None] = '99bf6cde3203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('campaign_contacts', sa.Column('next_follow_up_scheduled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('campaign_contacts', 'next_follow_up_scheduled_at')