"""update_prospect_status_enum_v1

Revision ID: 178352eee4fc
Revises: cee597a7e7c1
Create Date: 2026-05-27 17:21:00.294197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '178352eee4fc'
down_revision: Union[str, Sequence[str], None] = 'cee597a7e7c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE prospectstatus RENAME TO prospectstatus_old")
    op.execute("CREATE TYPE prospectstatus AS ENUM ('new', 'contacted', 'oven', 'fridge', 'trash', 'converted')")
    
    op.execute("ALTER TABLE prospects ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE prospects
        ALTER COLUMN status TYPE prospectstatus
        USING (
            CASE status::text
               WHEN 'qualified' THEN 'oven'
               WHEN 'negotiation' THEN 'oven'
               WHEN 'proposal_sent' THEN 'fridge'
               WHEN 'closed_lost' THEN 'trash'
               WHEN 'closed_won' THEN 'converted'
               ELSE status::text
            END
        )::prospectstatus
    """)
    op.execute("ALTER TABLE prospects ALTER COLUMN status SET DEFAULT 'new'::prospectstatus")
    op.execute("DROP TYPE prospectstatus_old")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE prospectstatus RENAME TO prospectstatus_new")
    op.execute("CREATE TYPE prospectstatus AS ENUM ('new', 'contacted', 'qualified', 'proposal_sent', 'negotiation', 'closed_won', 'closed_lost')")

    op.execute("ALTER TABLE prospects ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE prospects
        ALTER COLUMN status TYPE prospectstatus
        USING (
            CASE status::text
               WHEN 'oven' THEN 'qualified'
               WHEN 'fridge' THEN 'proposal_sent'
               WHEN 'trash' THEN 'closed_lost'
               WHEN 'converted' THEN 'closed_won'
               ELSE status::text
            END
        )::prospectstatus
    """)
    op.execute("ALTER TABLE prospects ALTER COLUMN status SET DEFAULT 'new'::prospectstatus")
    op.execute("DROP TYPE prospectstatus_new")
    
