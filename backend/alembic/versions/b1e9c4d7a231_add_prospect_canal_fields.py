"""add_prospect_canal_fields

Revision ID: b1e9c4d7a231
Revises: ad3f609ffbd9
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1e9c4d7a231'
down_revision: Union[str, Sequence[str], None] = 'ad3f609ffbd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

prospect_canal_enum = sa.Enum(
    'trade_show',
    'linkedin',
    'referral',
    'emailing',
    'inbound',
    'other',
    name='prospectcanal'
)

def upgrade() -> None:
  """Upgrade schema."""
  bind = op.get_bind()
  prospect_canal_enum.create(bind, checkfirst=True)

  op.add_column(
    "prospects",
    sa.Column("canal", prospect_canal_enum, nullable=True)
  )
  op.add_column(
    "prospects",
    sa.Column("canal_detail", sa.String(length=255), nullable=True)
  )
  op.create_index(
    "ix_prospects_user_canal",
    "prospects",
    ["user_id", "canal"],
    unique=False,
  )

def downgrade() -> None:
  """Downgrade schema."""
  op.drop_index("ix_prospects_user_canal", table_name="prospects")
  op.drop_column("prospects", "canal_detail")
  op.drop_column("prospects", "canal")
  
  bind = op.get_bind()
  prospect_canal_enum.drop(bind, checkfirst=True)