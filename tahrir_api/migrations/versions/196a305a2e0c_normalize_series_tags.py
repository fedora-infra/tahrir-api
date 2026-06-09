"""replace series tags with association table

Revision ID: 196a305a2e0c
Revises: 1013e1694fa2
Create Date: 2026-05-25 18:43:10.750442
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "196a305a2e0c"
down_revision = "1013e1694fa2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "series_tags",
        sa.Column("series_id", sa.Unicode(length=128), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["series_id"], ["series.id"], name=op.f("fk_series_tags_series_id_series")
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], name=op.f("fk_series_tags_tag_id_tags")),
        sa.PrimaryKeyConstraint("series_id", "tag_id", name=op.f("pk_series_tags")),
    )

    connection = op.get_bind()
    series = connection.execute(
        sa.text("SELECT id, tags FROM series WHERE tags IS NOT NULL AND tags != ''")
    ).fetchall()

    for series_id, tags in series:
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
                    INSERT INTO series_tags (series_id, tag_id)
                    VALUES (:series_id, :tag_id)
                    """),
                {"series_id": series_id, "tag_id": tag_id},
            )

    op.drop_column("series", "tags")


def downgrade():
    op.add_column("series", sa.Column("tags", sa.Unicode(length=128), nullable=True))

    connection = op.get_bind()
    series_ids = connection.execute(sa.text("SELECT id FROM series")).fetchall()

    for (series_id,) in series_ids:
        tag_rows = connection.execute(
            sa.text("""
                SELECT tags.name
                FROM tags
                JOIN series_tags ON tags.id = series_tags.tag_id
                WHERE series_tags.series_id = :series_id
                ORDER BY tags.name
                """),
            {"series_id": series_id},
        ).fetchall()
        tag_string = ", ".join([row[0] for row in tag_rows])

        connection.execute(
            sa.text("UPDATE series SET tags = :tags WHERE id = :series_id"),
            {"tags": tag_string, "series_id": series_id},
        )

    op.drop_table("series_tags")
