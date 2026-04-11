"""Normalize tags into separate tables

Revision ID: b416f5f62e33
Revises: 459d4cc47d13
Create Date: 2026-04-11 00:44:19.634395
"""

import sqlalchemy as sa
from alembic import op



# revision identifiers, used by Alembic.
revision = 'b416f5f62e33'
down_revision = '459d4cc47d13'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tags')),
        sa.UniqueConstraint('name', name=op.f('uq_tags_name'))
    )
    
    op.create_table('badge_tags',
        sa.Column('badge_id', sa.Unicode(length=128), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], name=op.f('fk_badge_tags_badge_id_badges'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_badge_tags_tag_id_tags'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('badge_id', 'tag_id', name=op.f('pk_badge_tags'))
    )

    op.create_table('series_tags',
        sa.Column('series_id', sa.Unicode(length=128), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], name=op.f('fk_series_tags_series_id_series'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_series_tags_tag_id_tags'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('series_id', 'tag_id', name=op.f('pk_series_tags'))
    )

    with op.batch_alter_table('badges', schema=None) as batch_op:
        batch_op.drop_column('tags')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('tags')


def downgrade():
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tags', sa.Unicode(length=128), nullable=True))

    with op.batch_alter_table('badges', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tags', sa.Unicode(length=128), nullable=True))

    op.drop_table('series_tags')
    op.drop_table('badge_tags')
    op.drop_table('tags')
    # ### end Alembic commands ###
