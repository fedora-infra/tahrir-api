"""add obsolete rarity tier for legacy badges

Revision ID: 034fa28d186e
Revises: c8dbbb6c717e
Create Date: 2026-08-20 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "034fa28d186e"
down_revision = "c8dbbb6c717e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("INSERT INTO rarities (name, lower_limit, upper_limit) VALUES ('O', 0, 0)")


def downgrade():
    op.execute(
        "UPDATE badges SET rarity_id = NULL"
        " WHERE rarity_id = (SELECT id FROM rarities WHERE name = 'O')"
    )
    op.execute("DELETE FROM rarities WHERE name = 'O'")
