"""add_kinde_id_to_users

Revision ID: 82015c1c2c01
Revises: 5c6d7e8f9a0b
Create Date: 2026-01-14 18:19:41.227885+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82015c1c2c01'
down_revision: Union[str, None] = '5c6d7e8f9a0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add kinde_id column to users table
    op.add_column('users', sa.Column('kinde_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_kinde_id'), 'users', ['kinde_id'], unique=True)
    
    # Make hashed_password nullable for Kinde users
    op.alter_column('users', 'hashed_password', nullable=True)


def downgrade() -> None:
    # Remove kinde_id column and index
    op.drop_index(op.f('ix_users_kinde_id'), table_name='users')
    op.drop_column('users', 'kinde_id')
    
    # Revert hashed_password to non-nullable
    op.alter_column('users', 'hashed_password', nullable=False)