"""add_campaign_builder_fields

Revision ID: c4f2a6d8b901
Revises: b1e9c4d7a231
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c4f2a6d8b901"
down_revision: Union[str, Sequence[str], None] = "b1e9c4d7a231"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

campaign_source_enum = sa.Enum(
    "trade_show",
    "ride_along",
    "outreach",
    name="campaignsource"
)

def upgrade() -> None:
    bind = op.get_bind()
    campaign_source_enum.create(bind, checkfirst=True)

    op.add_column(
        "campaigns",
        sa.Column("campaign_source", campaign_source_enum, nullable=False, server_default="trade_show")
    )
    op.add_column(
        "campaigns",
        sa.Column("is_distributor_show", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        "campaigns",
        sa.Column("distributor_company_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "campaigns",
        sa.Column("auto_cc_sales_rep", sa.Boolean(), nullable=False, server_default=sa.false())
    )

    op.add_column(
        "campaigns",
        sa.Column("company_intro_text", sa.Text(), nullable=True)
    )
    op.add_column(
        "campaigns",
        sa.Column("catalog_pitch_text", sa.Text(), nullable=True)
    )

    op.add_column(
        "campaigns",
        sa.Column("offer_samples", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        "campaigns",
        sa.Column("samples_note", sa.Text(), nullable=True)
    ) 

    op.add_column(
        "campaigns",
        sa.Column("segment_note_global", sa.Text(), nullable=True)
    )
    op.add_column(
        "campaigns",
        sa.Column("segment_note_restaurant", sa.Text(), nullable=True)
    )
    op.add_column(
        "campaigns",
        sa.Column("segment_note_industry", sa.Text(), nullable=True)
    )
    op.add_column(
        "campaigns",
        sa.Column("segment_note_retail", sa.Text(), nullable=True)
    )

    op.create_foreign_key(
        "fk_campaigns_distributor_company_id",
        "campaigns",
        "companies",
        ["distributor_company_id"],
        ["id"],
        ondelete="SET NULL"
    )

    # retirer server defaults runtime
    op.alter_column("campaigns", "campaign_source", server_default=None)
    op.alter_column("campaigns", "is_distributor_show", server_default=None)
    op.alter_column("campaigns", "auto_cc_sales_rep", server_default=None)
    op.alter_column("campaigns", "offer_samples", server_default=None)

def downgrade() -> None:
    op.drop_constraint("fk_campaigns_distributor_company_id", "campaigns", type_="foreignkey")

    op.drop_column("campaigns", "segment_note_retail")
    op.drop_column("campaigns", "segment_note_industry")
    op.drop_column("campaigns", "segment_note_restaurant")
    op.drop_column("campaigns", "segment_note_global")
    op.drop_column("campaigns", "samples_note")
    op.drop_column("campaigns", "offer_samples")
    op.drop_column("campaigns", "catalog_pitch_text")
    op.drop_column("campaigns", "company_intro_text")
    op.drop_column("campaigns", "auto_cc_sales_rep")
    op.drop_column("campaigns", "distributor_company_id")
    op.drop_column("campaigns", "is_distributor_show")
    op.drop_column("campaigns", "campaign_source")

    bind = op.get_bind()
    campaign_source_enum.drop(bind, checkfirst=True)
