"""fix foreign key mismatch

Revision ID: 16943d9088cf
Revises: 24282792d72a
Create Date: 2013-06-23 22:55:47.775736

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "16943d9088cf"
down_revision = "24282792d72a"


def upgrade():
    op.alter_column("invitations", "created_by", type_=sa.Integer)


def downgrade():
    op.alter_column("invitations", "created_by", type_=sa.Unicode(128))
