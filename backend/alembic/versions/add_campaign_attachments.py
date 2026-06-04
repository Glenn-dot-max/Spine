"""add campaign attachment paths

Revision ID: add_campaign_attachments
Revises: c4f2a6d8b901
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_campaign_attachments'
down_revision = 'c4f2a6d8b901'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('campaigns', sa.Column('attachment_paths', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('campaigns', 'attachment_paths')