"""add_meesho_credentials_to_users

Revision ID: 9a8b7c6d5e4f
Revises: 82015c1c2c01
Create Date: 2026-01-25 23:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, None] = '82015c1c2c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Meesho account linking fields to users table
    op.add_column('users', sa.Column('meesho_supplier_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('meesho_identifier', sa.String(), nullable=True))
    op.add_column('users', sa.Column('meesho_connect_sid_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('meesho_browser_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('meesho_linked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove Meesho account linking fields
    op.drop_column('users', 'meesho_linked_at')
    op.drop_column('users', 'meesho_browser_id')
    op.drop_column('users', 'meesho_connect_sid_encrypted')
    op.drop_column('users', 'meesho_identifier')
    op.drop_column('users', 'meesho_supplier_id')
