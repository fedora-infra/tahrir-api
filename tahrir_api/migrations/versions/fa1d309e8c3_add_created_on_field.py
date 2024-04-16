"""Add created_on field to issuers table.

Revision ID: fa1d309e8c3
Revises: 420c02357a1b
Create Date: 2013-06-10 12:30:31.850641

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "fa1d309e8c3"
down_revision = "420c02357a1b"


def upgrade():
    op.add_column("issuers", sa.Column("created_on", sa.DateTime, nullable=False))


def downgrade():
    # This will fail if using SQLite. The transaction will
    # be rolled back.
    op.drop_column("issuers", "created_on")
