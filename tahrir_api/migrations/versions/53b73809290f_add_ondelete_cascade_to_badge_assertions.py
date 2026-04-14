"""Add ondelete cascade to badge assertions

Revision ID: 53b73809290f
Revises: 459d4cc47d13
Create Date: 2026-04-10 23:02:35.121330
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "53b73809290f"
down_revision = "459d4cc47d13"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assertions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_assertions_badge_id_badges", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_assertions_badge_id_badges", "badges", ["badge_id"], ["id"], ondelete="CASCADE"
        )


def downgrade():
    with op.batch_alter_table("assertions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_assertions_badge_id_badges", type_="foreignkey")
        batch_op.create_foreign_key("fk_assertions_badge_id_badges", "badges", ["badge_id"], ["id"])
