"""Add a rank column to the Person table.

Revision ID: 139ec7ed17b7
Revises: 3c7fd5b4e2c2
Create Date: 2013-08-16 12:06:00.092052

"""

# revision identifiers, used by Alembic.
revision = '139ec7ed17b7'
down_revision = '3c7fd5b4e2c2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('persons', sa.Column('rank', sa.Integer, default=None))


def downgrade():
    op.drop_column('persons', 'rank')
