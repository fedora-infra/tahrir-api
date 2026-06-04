"""add cascade delete to all badge FK references

Revision ID: dc308dc04b85
Revises: 30c14a7fb2bd
Create Date: 2026-05-29 13:20:26.910718
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "dc308dc04b85"
down_revision = "5b1e956d70b5"
branch_labels = None
depends_on = None


def upgrade():
    # 1. assertions
    op.drop_constraint("assertions_badge_id_fkey", "assertions", type_="foreignkey")
    op.create_foreign_key(
        "assertions_badge_id_fkey", "assertions", "badges", ["badge_id"], ["id"], ondelete="CASCADE"
    )

    # 2. badge_tags
    op.drop_constraint("fk_badge_tags_badge_id_badges", "badge_tags", type_="foreignkey")
    op.create_foreign_key(
        "fk_badge_tags_badge_id_badges",
        "badge_tags",
        "badges",
        ["badge_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3. authorizations
    op.drop_constraint("authorizations_badge_id_fkey", "authorizations", type_="foreignkey")
    op.create_foreign_key(
        "authorizations_badge_id_fkey",
        "authorizations",
        "badges",
        ["badge_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. current_values
    op.drop_constraint("fk_current_values_badge_id_badges", "current_values", type_="foreignkey")
    op.create_foreign_key(
        "fk_current_values_badge_id_badges",
        "current_values",
        "badges",
        ["badge_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. invitations
    op.drop_constraint("invitations_badge_id_fkey", "invitations", type_="foreignkey")
    op.create_foreign_key(
        "invitations_badge_id_fkey",
        "invitations",
        "badges",
        ["badge_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 6. milestone
    op.drop_constraint("milestone_badge_id_fkey", "milestone", type_="foreignkey")
    op.create_foreign_key(
        "milestone_badge_id_fkey", "milestone", "badges", ["badge_id"], ["id"], ondelete="CASCADE"
    )


def downgrade():
    op.drop_constraint("assertions_badge_id_fkey", "assertions", type_="foreignkey")
    op.create_foreign_key("assertions_badge_id_fkey", "assertions", "badges", ["badge_id"], ["id"])

    op.drop_constraint("fk_badge_tags_badge_id_badges", "badge_tags", type_="foreignkey")
    op.create_foreign_key(
        "fk_badge_tags_badge_id_badges", "badge_tags", "badges", ["badge_id"], ["id"]
    )

    op.drop_constraint("authorizations_badge_id_fkey", "authorizations", type_="foreignkey")
    op.create_foreign_key(
        "authorizations_badge_id_fkey", "authorizations", "badges", ["badge_id"], ["id"]
    )

    op.drop_constraint("fk_current_values_badge_id_badges", "current_values", type_="foreignkey")
    op.create_foreign_key(
        "fk_current_values_badge_id_badges", "current_values", "badges", ["badge_id"], ["id"]
    )

    op.drop_constraint("invitations_badge_id_fkey", "invitations", type_="foreignkey")
    op.create_foreign_key(
        "invitations_badge_id_fkey", "invitations", "badges", ["badge_id"], ["id"]
    )

    op.drop_constraint("milestone_badge_id_fkey", "milestone", type_="foreignkey")
    op.create_foreign_key("milestone_badge_id_fkey", "milestone", "badges", ["badge_id"], ["id"])
