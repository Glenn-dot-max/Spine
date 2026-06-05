"""make distributor_catalog company_id optional

Revision ID: make_catalog_company_optional
Revises: add_distributor_catalog_pdf
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'make_catalog_company_optional'
down_revision = 'add_distributor_catalog_pdf'
branch_labels = None
depends_on = None

def upgrade():
    # Rendre company_id nullable
    op.alter_column('distributor_catalogs', 'company_id', nullable=True)
    # Supprime l'unique constraint existante (incompatible avec nullable)
    op.drop_constraint('uq_catalog_user_company', 'distributor_catalogs', type_='unique')

def downgrade():
    op.alter_column('distributor_catalogs', 'company_id', nullable=False)
    op.create_unique_constraint('uq_catalog_user_company', 'distributor_catalogs', ['user_id', 'company_id'])
    