"""Normalize badge tags into a separate table.

Revision ID: a1b2c3d4e5f6
Revises: 459d4cc47d13
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op


revision = "a1b2c3d4e5f6"
down_revision = "459d4cc47d13"


def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Unicode(128), nullable=False, unique=True),
    )

    op.create_table(
        "badge_tags",
        sa.Column("badge_id", sa.Unicode(128), sa.ForeignKey("badges.id")),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tags.id")),
    )

    connection = op.get_bind()
    badges = connection.execute(sa.text("SELECT id, tags FROM badges WHERE tags IS NOT NULL"))
    for badge_id, tags_str in badges:
        for tag_name in [t.strip() for t in tags_str.split(",") if t.strip()]:
            existing = connection.execute(
                sa.text("SELECT id FROM tags WHERE name = :name"),
                {"name": tag_name},
            ).fetchone()
            if not existing:
                connection.execute(
                    sa.text("INSERT INTO tags (name) VALUES (:name)"),
                    {"name": tag_name},
                )
            tag_id = connection.execute(
                sa.text("SELECT id FROM tags WHERE name = :name"),
                {"name": tag_name},
            ).fetchone()[0]
            connection.execute(
                sa.text("INSERT INTO badge_tags (badge_id, tag_id) VALUES (:badge_id, :tag_id)"),
                {"badge_id": badge_id, "tag_id": tag_id},
            )

    op.drop_column("badges", "tags")


def downgrade():
    op.add_column("badges", sa.Column("tags", sa.Unicode(128)))
    op.drop_table("badge_tags")
    op.drop_table("tags")
