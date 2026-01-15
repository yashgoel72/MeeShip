"""Add payments infrastructure for Razorpay integration

Revision ID: 4a5b6c7d8e9f
Revises: 3b2c4d5e6f70
Create Date: 2026-01-14 15:40:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4a5b6c7d8e9f"
down_revision: Union[str, None] = "3b2c4d5e6f70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add credits column to users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("credits", sa.Integer(), nullable=False, server_default=sa.text("0"))
        )

    # Create orders table
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("razorpay_order_id", sa.String(), unique=True, nullable=False),
        sa.Column("razorpay_payment_id", sa.String(), unique=True, nullable=True),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("credits_purchased", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'created'")),
        sa.Column("receipt", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_razorpay_order_id", "orders", ["razorpay_order_id"])

    # Create webhook_logs table
    op.create_table(
        "webhook_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(), unique=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_webhook_logs_event_id", "webhook_logs", ["event_id"])


def downgrade() -> None:
    # Drop webhook_logs table
    op.drop_index("ix_webhook_logs_event_id", "webhook_logs")
    op.drop_table("webhook_logs")

    # Drop orders table
    op.drop_index("ix_orders_razorpay_order_id", "orders")
    op.drop_index("ix_orders_user_id", "orders")
    op.drop_table("orders")

    # Remove credits column from users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("credits")