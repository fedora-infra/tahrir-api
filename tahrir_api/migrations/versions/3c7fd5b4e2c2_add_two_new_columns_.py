"""Add two new columns for Person.

Revision ID: 3c7fd5b4e2c2
Revises: 24282792d72a
Create Date: 2013-06-26 14:46:28.361709

"""

import datetime

import sqlalchemy as sa
from alembic import op

import tahrir_api


# revision identifiers, used by Alembic.
revision = "3c7fd5b4e2c2"
down_revision = "16943d9088cf"


def upgrade():
    op.add_column("persons", sa.Column("created_on", sa.DateTime()))
    op.add_column("persons", sa.Column("opt_out", sa.Boolean()))

    # We have to do this manually because I can't figure out how to make
    # alembic apply defaults to sqlite.
    engine = op.get_bind().engine
    session_maker = sa.orm.sessionmaker(bind=engine)
    session = sa.orm.scoped_session(session_maker)
    persons = session.query(tahrir_api.model.Person).all()
    for person in persons:
        # Set our defaults
        person.created_on = datetime.datetime.now()
        person.opt_out = False
    session.commit()


def downgrade():
    op.drop_column("persons", "opt_out")
    op.drop_column("persons", "created_on")
