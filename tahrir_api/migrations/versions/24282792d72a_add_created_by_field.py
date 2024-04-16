"""Add created_by field to invitations.

Revision ID: 24282792d72a
Revises: 5791a2b9fb6a
Create Date: 2013-06-10 15:51:02.288685

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "24282792d72a"
down_revision = "5791a2b9fb6a"


def upgrade():
    op.add_column(
        "invitations",
        sa.Column("created_by", sa.Unicode(128), sa.ForeignKey("persons.id"), nullable=False),
    )


def downgrade():
    # Downgrade will fail if using SQLite. The transaction will
    # be rolled back as per env.py.
    op.drop_column("invitations", "created_by")
