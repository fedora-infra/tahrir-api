"""add authz table

Revision ID: ce541796a7
Revises: 4099fa344171
Create Date: 2013-12-13 15:30:16.576871

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "ce541796a7"
down_revision = "4099fa344171"


def upgrade():
    op.create_table(
        "authorizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("badge_id", sa.Unicode(length=128), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["badge_id"], ["badges.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("authorizations")
