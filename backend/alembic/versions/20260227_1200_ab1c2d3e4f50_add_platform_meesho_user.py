"""add_platform_meesho_user

Revision ID: ab1c2d3e4f50
Revises: 9a8b7c6d5e4f
Create Date: 2026-02-27 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = 'ab1c2d3e4f50'
down_revision: Union[str, None] = '9a8b7c6d5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLATFORM_USER_EMAIL = "jaishreeshyamindustries134@gmail.com"


def upgrade() -> None:
    # Insert the platform dummy user row using raw SQL to handle UUID type correctly
    platform_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, PLATFORM_USER_EMAIL))
    op.execute(
        sa.text(
            "INSERT INTO users (id, email, full_name, hashed_password, kinde_id, is_active, email_verified, credits) "
            "VALUES (CAST(:platform_id AS uuid), :email, :full_name, NULL, NULL, TRUE, TRUE, 0) "
            "ON CONFLICT (id) DO NOTHING"
        ).bindparams(
            platform_id=platform_id,
            email=PLATFORM_USER_EMAIL,
            full_name='Platform Meesho Account',
        )
    )


def downgrade() -> None:
    # Remove the platform user
    op.execute(
        f"DELETE FROM users WHERE email = '{PLATFORM_USER_EMAIL}'"
    )
