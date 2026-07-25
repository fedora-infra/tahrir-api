"""Add indexes on foreign key columns

Revision ID: c8dbbb6c717e
Revises: 53b73809290f
Create Date: 2026-07-25 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c8dbbb6c717e"
down_revision = "53b73809290f"
branch_labels = None
depends_on = None

FK_INDEXES = [
    ("ix_badges_issuer_id", "badges", ["issuer_id"]),
    ("ix_series_team_id", "series", ["team_id"]),
    ("ix_milestone_badge_id", "milestone", ["badge_id"]),
    ("ix_milestone_series_id", "milestone", ["series_id"]),
    ("ix_invitations_badge_id", "invitations", ["badge_id"]),
    ("ix_invitations_created_by", "invitations", ["created_by"]),
    ("ix_authorizations_badge_id", "authorizations", ["badge_id"]),
    ("ix_authorizations_person_id", "authorizations", ["person_id"]),
    ("ix_assertions_badge_id", "assertions", ["badge_id"]),
    ("ix_assertions_person_id", "assertions", ["person_id"]),
]


def upgrade():
    for index_name, table_name, columns in FK_INDEXES:
        op.create_index(index_name, table_name, columns)


def downgrade():
    for index_name, table_name, _columns in FK_INDEXES:
        op.drop_index(index_name, table_name)
