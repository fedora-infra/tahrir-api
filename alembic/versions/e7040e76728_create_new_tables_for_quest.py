"""Create new tables for Quest

Revision ID: e7040e76728
Revises: 508367dcbbb5
Create Date: 2016-09-02 20:51:14.951460

"""

# revision identifiers, used by Alembic.
revision = 'e7040e76728'
down_revision = '508367dcbbb5'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        'team',
        sa.Column('id', sa.Unicode(length=128), nullable=False),
        sa.Column('name', sa.Unicode(length=128), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'series',
        sa.Column('id', sa.Unicode(length=128), nullable=False),
        sa.Column('name', sa.Unicode(length=128), nullable=False),
        sa.Column('description', sa.Unicode(length=128), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('tags', sa.Unicode(length=128), nullable=True),
        sa.Column('team_id', sa.Unicode(length=128), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'milestone',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('badge_id', sa.Unicode(length=128), nullable=False),
        sa.Column('series_id', sa.Unicode(length=128), nullable=False),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('position', 'badge_id', 'series_id')
    )


def downgrade():

    op.drop_table('milestone')
    op.drop_table('series')
    op.drop_table('team')
