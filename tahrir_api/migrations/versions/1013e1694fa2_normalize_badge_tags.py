"""refactor badge tags to normalized table

Revision ID: 1013e1694fa2
Revises: caeca369a786
Create Date: 2026-05-24 14:24:40.674192
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "1013e1694fa2"
down_revision = "caeca369a786"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Unicode(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tags")),
        sa.UniqueConstraint("name", name=op.f("uq_tags_name")),
    )
    op.create_table(
        "badge_tags",
        sa.Column("badge_id", sa.Unicode(length=128), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["badge_id"], ["badges.id"], name=op.f("fk_badge_tags_badge_id_badges")
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], name=op.f("fk_badge_tags_tag_id_tags")),
        sa.PrimaryKeyConstraint("badge_id", "tag_id", name=op.f("pk_badge_tags")),
    )

    connection = op.get_bind()
    badges = connection.execute(
        sa.text("SELECT id, tags FROM badges WHERE tags IS NOT NULL AND tags != ''")
    ).fetchall()

    for badge_id, tags in badges:
        tag_names = []
        for tag_name in tags.split(","):
            tag_name = tag_name.strip()
            if tag_name and tag_name not in tag_names:
                tag_names.append(tag_name)

        for tag_name in tag_names:
            tag_id = connection.execute(
                sa.text("SELECT id FROM tags WHERE name = :name"),
                {"name": tag_name},
            ).scalar()

            if tag_id is None:
                tag_id = connection.execute(
                    sa.text("INSERT INTO tags (name) VALUES (:name) RETURNING id"),
                    {"name": tag_name},
                ).scalar()

            connection.execute(
                sa.text("""
                    INSERT INTO badge_tags (badge_id, tag_id)
                    VALUES (:badge_id, :tag_id)
                    """),
                {"badge_id": badge_id, "tag_id": tag_id},
            )

    op.drop_column("badges", "tags")


def downgrade():
    op.add_column("badges", sa.Column("tags", sa.Unicode(length=128), nullable=True))

    connection = op.get_bind()
    badge_ids = connection.execute(sa.text("SELECT id FROM badges")).fetchall()

    for (badge_id,) in badge_ids:
        tag_rows = connection.execute(
            sa.text("""
                SELECT tags.name
                FROM tags
                JOIN badge_tags ON tags.id = badge_tags.tag_id
                WHERE badge_tags.badge_id = :badge_id
                ORDER BY tags.name
                """),
            {"badge_id": badge_id},
        ).fetchall()
        tag_string = ", ".join([row[0] for row in tag_rows])

        connection.execute(
            sa.text("UPDATE badges SET tags = :tags WHERE id = :badge_id"),
            {"tags": tag_string, "badge_id": badge_id},
        )

    op.drop_table("badge_tags")
    op.drop_table("tags")
