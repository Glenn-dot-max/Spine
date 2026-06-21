"""add company chain_level and end_user_type

Revision ID: a1b2c3d4e5f6
Revises: make_catalog_company_optional
Create date: 2026-06-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'make_catalog_company_optional'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop old columns
    op.drop_column('companies', 'type_structure')
    op.drop_column('companies', 'type_contact')

    # Drop old enum types (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS structuretype")
    op.execute("DROP TYPE IF EXISTS contacttype")

    # Create new enum types
    op.execute("""
        CREATE TYPE chainlevel AS ENUM (
               'distributor', 'importer', 'broker', 'end_user', 'other'
        )
    """)
    op.execute("""
        CREATE TYPE endusertype AS ENUM (
               'restaurant', 'hotel', 'franchise', 'country_club',
                'catering', 'institution', 'retail', 'other'
        )
    """)

    # Add new columns
    op.add_column('companies', sa.Column(
        'chain_level',
        sa.Enum('distributor', 'importer', 'broker', 'end_user', 'other', name='chainlevel'),
        nullable=True
    ))
    op.add_column('companies', sa.Column(
        'end_user_type',
        sa.Enum('restaurant', 'hotel', 'franchise', 'country_club', 'catering', 'institution', 'retail', 'other', name='endusertype'),
        nullable=True
    ))

def downgrade() -> None:
    op.drop_column('companies', 'chain_level')
    op.drop_column('companies', 'end_user_type')
    op.execute("DROP TYPE IF EXISTS chainlevel")
    op.execute("DROP TYPE IF EXISTS endusertype")

    op.execute("CREATE TYPE structuretype AS ENUM ('retail', 'foodservice', 'industry', 'other')")
    op.execute("CREATE TYPE contacttype AS ENUM ('distributor', 'restaurant', 'factory', 'consultant', 'retailer', 'other')")

    op.add_column('companies', sa.Column('type_structure', sa.Enum(name='structuretype'), nullable=True))
    op.add_column('companies', sa.Column('type_contact', sa.Enum(name='contacttype'), nullable=True))