"""issued_for

Revision ID: 2879ed5a6297
Revises: ce541796a7
Create Date: 2014-03-04 11:04:31.024949

"""

# revision identifiers, used by Alembic.
revision = '2879ed5a6297'
down_revision = 'ce541796a7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('assertions', sa.Column('issued_for', sa.Unicode(256)))


def downgrade():
    # This will fail if using SQLite. The transaction will
    # be rolled back.
    op.drop_column('assertions', 'issued_for')
