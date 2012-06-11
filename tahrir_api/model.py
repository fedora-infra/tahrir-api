import hashlib

from sqlalchemy import (
    Column,
    BigInteger,
    DateTime,
    Unicode,
    ForeignKey,
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    backref,
)


DeclarativeBase = declarative_base()


class Issuer(DeclarativeBase):
    __tablename__ = 'issuers'
    id = Column(BigInteger, primary_key=True)
    origin = Column(Unicode(128), nullable=False)
    name = Column(Unicode(128), nullable=False, unique=True)
    org = Column(Unicode(128), nullable=False)
    contact = Column(Unicode(128), nullable=False)
    badges = relationship("Badge", backref="issuer")

    def __unicode__(self):
        return self.name

    def __json__(self):
        return dict(
            origin=self.origin,
            name=self.name,
            org=self.org,
            contact=self.contact,
        )


def badge_id_default(context):
    return context.current_parameters['name'].lower().replace(' ', '-')


class Badge(DeclarativeBase):
    __tablename__ = 'badges'
    id = Column(Unicode(128), primary_key=True, default=badge_id_default)
    name = Column(Unicode(128), nullable=False, unique=True)
    image = Column(Unicode(128), nullable=False)
    description = Column(Unicode(128), nullable=False)
    criteria = Column(Unicode(128), nullable=False)
    assertions = relationship("Assertion", backref="badge")
    issuer_id = Column(BigInteger, ForeignKey('issuers.id'), nullable=False)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return dict(
            version="0.5.0",
            name=self.name,
            image="/pngs/" + self.image,
            description=self.description,
            criteria=self.criteria,
            issuer=self.issuer.__json__(),
        )


class Person(DeclarativeBase):
    __tablename__ = 'persons'
    id = Column(BigInteger, primary_key=True)
    email = Column(Unicode(128), nullable=False, unique=True)
    assertions = relationship("Assertion", backref="person")

    @property
    def gravatar_link(self):
        d, s = 'mm', 24
        hash = hashlib.md5(self.email).hexdigest()
        url = "http://www.gravatar.com/avatar/%s?s=%i&d=%s" % (hash, s, d)
        return url

    def __unicode__(self):
        return self.email


def recipient_default(context):
    Session = sessionmaker(context.engine)()
    person_id = context.current_parameters['person_id']
    person = Session.query(Person).filter_by(id=person_id).one()
    return hashlib.sha256(
        person.email + context.current_parameters['salt']
    ).hexdigest()


def salt_default(context):
    # TODO -- some how we need to get this value from the config.  :)
    return "beefy"


def assertion_id_default(context):
    person_id = context.current_parameters['person_id']
    badge_id = context.current_parameters['badge_id']
    return "%r -> %r" % (badge_id, person_id)


class Assertion(DeclarativeBase):
    __tablename__ = 'assertions'
    id = Column(Unicode(128), primary_key=True, unique=True,
                default=assertion_id_default)
    badge_id = Column(Unicode(128), ForeignKey('badges.id'), nullable=False)
    person_id = Column(BigInteger, ForeignKey('persons.id'), nullable=False)
    salt = Column(Unicode(128), nullable=False, default=salt_default)
    issued_on = Column(DateTime)

    recipient = Column(Unicode(256), nullable=False, default=recipient_default)
