"""add_oauth_providers

Revision ID: 8f0d352ea6cd
Revises: 0ef171628c44
Create Date: 2026-03-01 18:11:40.094582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f0d352ea6cd'
down_revision: Union[str, Sequence[str], None] = '0ef171628c44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Gmail Oauth
    op.add_column('users', sa.Column('gmail_connected', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('gmail_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('gmail_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('gmail_refresh_token', sa.String(), nullable=True))
    
    # Outlook Oauth
    op.add_column('users', sa.Column('outlook_connected', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('outlook_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('outlook_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('outlook_refresh_token', sa.String(), nullable=True))

    # Provider par défaut
    op.add_column('users', sa.Column('default_email_provider', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'default_email_provider')
    op.drop_column('users', 'outlook_refresh_token')
    op.drop_column('users', 'outlook_access_token')
    op.drop_column('users', 'outlook_email')
    op.drop_column('users', 'outlook_connected')
    op.drop_column('users', 'gmail_refresh_token')
    op.drop_column('users', 'gmail_access_token')
    op.drop_column('users', 'gmail_email')
    op.drop_column('users', 'gmail_connected')
