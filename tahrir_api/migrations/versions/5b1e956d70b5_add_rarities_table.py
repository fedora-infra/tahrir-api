"""add rarities table and rarity_id to badges

Revision ID: 5b1e956d70b5
Revises: caeca369a786
Create Date: 2026-05-21 16:57:28.719850
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b1e956d70b5"
down_revision = "196a305a2e0c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rarities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(8), nullable=False),
        sa.Column("lower_limit", sa.Float(), nullable=False),
        sa.Column("upper_limit", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.add_column(
        "badges",
        sa.Column("rarity_id", sa.Integer(), sa.ForeignKey("rarities.id"), nullable=True),
    )
    op.create_index("ix_badges_rarity_id", "badges", ["rarity_id"])


def downgrade():
    op.drop_index("ix_badges_rarity_id", table_name="badges")
    op.drop_column("badges", "rarity_id")
    op.drop_table("rarities")
