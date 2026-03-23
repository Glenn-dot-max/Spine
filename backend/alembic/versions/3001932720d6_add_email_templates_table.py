"""add_email_templates_table

Revision ID: 3001932720d6
Revises: 283243cb5559
Create Date: 2026-03-20 13:35:06.745559

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '3001932720d6'  # Garde le revision ID existant
down_revision = '283243cb5559'  # Garde le down_revision existant
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table email_templates
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subject_template', sa.String(length=500), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('variables', JSON, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Index pour performance
    op.create_index('ix_email_templates_user_id', 'email_templates', ['user_id'])
    op.create_index('ix_email_templates_name', 'email_templates', ['name'])
    op.create_index('ix_email_templates_category', 'email_templates', ['category'])
    
    # Index unique pour éviter les doublons (user_id + name)
    # NULL pour user_id = template global
    op.create_index(
        'ix_email_templates_user_name_unique',
        'email_templates',
        ['user_id', 'name'],
        unique=True
    )


def downgrade():
    op.drop_index('ix_email_templates_user_name_unique', table_name='email_templates')
    op.drop_index('ix_email_templates_category', table_name='email_templates')
    op.drop_index('ix_email_templates_name', table_name='email_templates')
    op.drop_index('ix_email_templates_user_id', table_name='email_templates')
    op.drop_table('email_templates')