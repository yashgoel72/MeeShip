"""Add credit expiry and pack_id fields

Revision ID: 5c6d7e8f9a0b
Revises: 4a5b6c7d8e9f
Create Date: 2026-01-14 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c6d7e8f9a0b'
down_revision: Union[str, None] = '4a5b6c7d8e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add credits_expires_at to users table
    op.add_column('users', sa.Column('credits_expires_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add pack_id to orders table
    op.add_column('orders', sa.Column('pack_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'pack_id')
    op.drop_column('users', 'credits_expires_at')
