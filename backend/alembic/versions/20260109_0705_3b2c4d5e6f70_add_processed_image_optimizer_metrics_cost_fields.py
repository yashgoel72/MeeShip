"""Add processed_images optimizer metrics and cost fields

Revision ID: 3b2c4d5e6f70
Revises: 868bb8651387
Create Date: 2026-01-09 07:05:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3b2c4d5e6f70"
down_revision: Union[str, None] = "868bb8651387"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("processed_images") as batch_op:
        # Input/output image metadata
        batch_op.add_column(sa.Column("input_size_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("output_size_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("input_width", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("input_height", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("output_width", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("output_height", sa.Integer(), nullable=True))

        # Optimization metrics
        batch_op.add_column(sa.Column("processing_time_ms", sa.Integer(), nullable=True))

        # Cost prediction inputs/outputs
        batch_op.add_column(sa.Column("actual_weight_g", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("volumetric_weight_g", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("billable_weight_g", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("shipping_cost_inr", sa.Integer(), nullable=True))

        # Status/error info
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default=sa.text("'success'"),
            )
        )
        batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))

        # Versioning / extended metrics (stored as JSON-serialized string)
        batch_op.add_column(sa.Column("optimizer_version", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("stage_metrics_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("processed_images") as batch_op:
        batch_op.drop_column("stage_metrics_json")
        batch_op.drop_column("optimizer_version")
        batch_op.drop_column("error_message")
        batch_op.drop_column("status")
        batch_op.drop_column("shipping_cost_inr")
        batch_op.drop_column("billable_weight_g")
        batch_op.drop_column("volumetric_weight_g")
        batch_op.drop_column("actual_weight_g")
        batch_op.drop_column("processing_time_ms")
        batch_op.drop_column("output_height")
        batch_op.drop_column("output_width")
        batch_op.drop_column("input_height")
        batch_op.drop_column("input_width")
        batch_op.drop_column("output_size_bytes")
        batch_op.drop_column("input_size_bytes")