"""add_response_tracking

Revision ID: 99bf6cde3203
Revises: f27366d10d8e
Create Date: 2026-03-14 11:03:09.717214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99bf6cde3203'
down_revision: Union[str, Sequence[str], None] = 'f27366d10d8e'  # ← CHANGÉ ICI
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('campaign_contacts', sa.Column('response_received_at', sa.DateTime(), nullable=True))
    op.add_column('campaign_contacts', sa.Column('last_response_content', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('campaign_contacts', 'last_response_content')
    op.drop_column('campaign_contacts', 'response_received_at')