"""Add created_on field to badges table.

Revision ID: 420c02357a1b
Revises: None
Create Date: 2013-06-09 22:23:32.519635

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "420c02357a1b"
down_revision = None


def upgrade():
    op.add_column("badges", sa.Column("created_on", sa.DateTime, nullable=False))


def downgrade():
    # This will fail if using SQLite. The transaction will
    # be rolled back.
    op.drop_column("badges", "created_on")
