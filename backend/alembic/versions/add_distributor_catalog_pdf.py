"""add pdf fields to distributor catalog

Revision ID: add_distributor_catalog_pdf
Revises: add_campaign_attachments
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_distributor_catalog_pdf'
down_revision = 'add_campaign_attachments'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('distributor_catalogs', sa.Column('pdf_path', sa.Text(), nullable=True))
    op.add_column('distributor_catalogs', sa.Column('pdf_filename', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('distributor_catalogs', 'pdf_filename')
    op.drop_column('distributor_catalogs', 'pdf_path')