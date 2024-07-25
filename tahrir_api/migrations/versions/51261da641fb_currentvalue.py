"""CurrentValue

Revision ID: 51261da641fb
Revises: 3d3fb9e59e7b
Create Date: 2024-07-23 15:27:48.303528
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "51261da641fb"
down_revision = "3d3fb9e59e7b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "current_values",
        sa.Column("badge_id", sa.Unicode(length=128), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("last_update", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["badge_id"], ["badges.id"], name=op.f("fk_current_values_badge_id_badges")
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["persons.id"], name=op.f("fk_current_values_person_id_persons")
        ),
        sa.PrimaryKeyConstraint("badge_id", "person_id", name=op.f("pk_current_values")),
    )


def downgrade():
    op.drop_table("current_values")
