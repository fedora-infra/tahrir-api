"""Add profile fields to persons.

Revision ID: 39583332f4ea
Revises: fa1d309e8c3
Create Date: 2013-06-10 12:33:45.319780

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "39583332f4ea"
down_revision = "fa1d309e8c3"


def upgrade():
    op.add_column("persons", sa.Column("nickname", sa.Text))
    op.add_column("persons", sa.Column("website", sa.Text))
    op.add_column("persons", sa.Column("bio", sa.Text))


def downgrade():
    # Downgrade will fail if using SQLite. The transaction will
    # be rolled back as per env.py.
    op.drop_column("persons", "nickname")
    op.drop_column("persons", "website")
    op.drop_column("persons", "bio")
