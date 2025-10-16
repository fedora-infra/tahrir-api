"""add index on assertions issued_on column

Revision ID: 459d4cc47d13
Revises: 51261da641fb
Create Date: 2025-10-18 09:06:20.131085
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "459d4cc47d13"
down_revision = "51261da641fb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_assertions_issued_on", "assertions", ["issued_on"])


def downgrade():
    op.drop_index("ix_assertions_issued_on", "assertions")
