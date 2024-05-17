"""Add Person.avatar

Revision ID: 3d3fb9e59e7b
Revises: e7040e76728
Create Date: 2024-05-17 13:47:31.271833
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "3d3fb9e59e7b"
down_revision = "e7040e76728"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("persons", sa.Column("_avatar", sa.Unicode(length=128), nullable=True))


def downgrade():
    op.drop_column("persons", "_avatar")
