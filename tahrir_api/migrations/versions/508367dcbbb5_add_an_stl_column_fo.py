"""Add an stl column for badges.

Revision ID: 508367dcbbb5
Revises: 2879ed5a6297
Create Date: 2014-07-11 09:36:33.211281

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "508367dcbbb5"
down_revision = "2879ed5a6297"


def upgrade():
    op.add_column("badges", sa.Column("stl", sa.Unicode(128)))


def downgrade():
    # Downgrade will fail if using SQLite. The transaction will
    # be rolled back as per env.py.
    op.drop_column("badges", "stl")
