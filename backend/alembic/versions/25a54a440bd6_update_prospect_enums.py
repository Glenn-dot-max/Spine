"""update_prospect_enums

Revision ID: xxxxx
Revises: 0ef171628c44
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxxxx'  # Auto-généré
down_revision = '0ef171628c44'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Mettre à jour l'enum ProspectSource
    op.execute("ALTER TYPE prospectsource RENAME TO prospectsource_old")
    op.execute("CREATE TYPE prospectsource AS ENUM ('trade_show', 'ride_along', 'referral', 'cold_outreach', 'inbound', 'other')")
    op.execute("ALTER TABLE prospects ALTER COLUMN source TYPE prospectsource USING source::text::prospectsource")
    op.execute("DROP TYPE prospectsource_old")
    
    # Mettre à jour l'enum ProspectStatus
    op.execute("ALTER TYPE prospectstatus RENAME TO prospectstatus_old")
    op.execute("CREATE TYPE prospectstatus AS ENUM ('new', 'contacted', 'qualified', 'proposal_sent', 'negotiation', 'closed_won', 'closed_lost')")
    op.execute("ALTER TABLE prospects ALTER COLUMN status TYPE prospectstatus USING status::text::prospectstatus")
    op.execute("DROP TYPE prospectstatus_old")

def downgrade() -> None:
    # Restaurer les anciens enums
    op.execute("ALTER TYPE prospectsource RENAME TO prospectsource_old")
    op.execute("CREATE TYPE prospectsource AS ENUM ('TRADE_SHOW', 'RIDE_ALONG', 'PROSPECTION', 'RECOMMENDATION', 'OTHER')")
    op.execute("ALTER TABLE prospects ALTER COLUMN source TYPE prospectsource USING source::text::prospectsource")
    op.execute("DROP TYPE prospectsource_old")
    
    op.execute("ALTER TYPE prospectstatus RENAME TO prospectstatus_old")
    op.execute("CREATE TYPE prospectstatus AS ENUM ('NEW', 'CONTACTED', 'RESPONDED', 'ARCHIVED')")
    op.execute("ALTER TABLE prospects ALTER COLUMN status TYPE prospectstatus USING status::text::prospectstatus")
    op.execute("DROP TYPE prospectstatus_old")