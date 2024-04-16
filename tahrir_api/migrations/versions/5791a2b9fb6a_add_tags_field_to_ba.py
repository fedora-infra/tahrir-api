"""Add tags field to badges.

Revision ID: 5791a2b9fb6a
Revises: 39583332f4ea
Create Date: 2013-06-10 13:05:40.130328

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "5791a2b9fb6a"
down_revision = "39583332f4ea"


def upgrade():
    op.add_column("badges", sa.Column("tags", sa.Text))


def downgrade():
    # Downgrade will fail if using SQLite. The transaction will
    # be rolled back as per env.py.
    op.drop_column("badges", "tags")
