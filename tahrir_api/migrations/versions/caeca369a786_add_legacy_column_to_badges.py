"""add legacy column to badges

Revision ID: caeca369a786
Revises: 459d4cc47d13
Create Date: 2026-05-20 12:52:05.752509
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "caeca369a786"
down_revision = "459d4cc47d13"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "badges",
        sa.Column("legacy", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("badges", "legacy")
