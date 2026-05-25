"""fix_prospect_email_unique_per_user

Revision ID: 2992995b13d6
Revises: 90849d859011
Create Date: 2026-05-25 16:16:31.793359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2992995b13d6'
down_revision: Union[str, Sequence[str], None] = '90849d859011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_constraint('prospects_email_key', 'prospects', type_='unique')
    op.create_unique_constraint('uq_prospects_email_user', 'prospects', ['email', 'user_id'])

def downgrade() -> None:
    op.drop_constraint('uq_prospects_email_user', 'prospects', type_='unique')
    op.create_unique_constraint('prospects_email_key', 'prospects', ['email'])
