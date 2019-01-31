import pygments
import simplejson
import hashlib
import uuid
import datetime
import time

import arrow

from sqlalchemy import Column, DateTime, Unicode, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, Boolean

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session, sessionmaker, relationship


from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DeclarativeBase = declarative_base()
DeclarativeBase.query = DBSession.query_property()


class Issuer(DeclarativeBase):
    __tablename__ = "issuers"
    id = Column(Integer, unique=True, primary_key=True)
    origin = Column(Unicode(128), nullable=False)
    name = Column(Unicode(128), nullable=False, unique=True)
    org = Column(Unicode(128), nullable=False)
    contact = Column(Unicode(128), nullable=False)
    badges = relationship("Badge", backref="issuer")
    created_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __unicode__(self):
        return str(self.name)

    __str__ = __unicode__

    def __json__(self):
        return dict(
            origin=self.origin,
            name=self.name,
            org=self.org,
            contact=self.contact,
            created_on=time.mktime(self.created_on.timetuple()),
        )


def generate_default_id(context):
    return context.current_parameters["name"].lower().replace(" ", "-")


class Badge(DeclarativeBase):
    __tablename__ = "badges"
    id = Column(Unicode(128), primary_key=True, default=generate_default_id)
    name = Column(Unicode(128), nullable=False, unique=True)
    image = Column(Unicode(128), nullable=False)
    stl = Column(Unicode(128))
    description = Column(Unicode(128), nullable=False)
    criteria = Column(Unicode(128), nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    milestone = relationship("Milestone", backref="badge")
    authorizations = relationship("Authorization", backref="badge")
    assertions = relationship("Assertion", backref="badge")
    invitations = relationship("Invitation", backref="badge")
    created_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    tags = Column(Unicode(128))

    def __unicode__(self):
        return str(self.name)

    __str__ = __unicode__

    def __json__(self):
        if self.image.startswith("http"):
            image = self.image
        else:
            image = "/pngs/" + self.image
        return dict(
            version="0.5.0",
            name=self.name,
            image=image,
            description=self.description,
            criteria=self.criteria,
            issuer=self.issuer.__json__(),
            created_on=time.mktime(self.created_on.timetuple()),
            tags=self.tags,
        )

    def authorized(self, person):
        """ Return true if a given person is authorized to admin a badge """
        for authz in self.authorizations:
            if authz.person == person:
                return True

        return False


class Team(DeclarativeBase):
    __tablename__ = "team"
    id = Column(Unicode(128), primary_key=True, default=generate_default_id)
    name = Column(Unicode(128), nullable=False, unique=True)
    series = relationship("Series", backref="team")
    created_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __json__(self):
        return dict(id=self.id, name=self.name, created_on=str(self.created_on))


class Series(DeclarativeBase):
    __tablename__ = "series"
    id = Column(Unicode(128), primary_key=True, default=generate_default_id)
    name = Column(Unicode(128), nullable=False, unique=True)
    description = Column(Unicode(128), nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    tags = Column(Unicode(128))
    milestone = relationship("Milestone", backref="series")
    team_id = Column(Unicode(128), ForeignKey("team.id"), nullable=False)

    def __json__(self):
        return dict(
            id=self.id,
            name=self.name,
            created_on=str(self.created_on),
            last_updated=str(self.last_updated),
            team=self.team.__json__(),
        )


class Milestone(DeclarativeBase):
    __tablename__ = "milestone"
    __table_args__ = (UniqueConstraint("position", "badge_id", "series_id"),)
    id = Column(Integer, unique=True, primary_key=True)
    position = Column(Integer, default=None)
    badge_id = Column(Unicode(128), ForeignKey("badges.id"), nullable=False)
    series_id = Column(Unicode(128), ForeignKey("series.id"), nullable=False)

    def __json__(self):
        return dict(
            position=self.position,
            badge=self.badge.__json__(),
            series_id=self.series.id,
        )


class Person(DeclarativeBase):
    __tablename__ = "persons"
    id = Column(Integer, unique=True, primary_key=True)
    email = Column(Unicode(128), nullable=False, unique=True)
    authorizations = relationship("Authorization", backref="person")
    assertions = relationship("Assertion", backref="person")
    nickname = Column(Unicode(128), unique=True)
    website = Column(Unicode(128))
    bio = Column(Unicode(140))
    created_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True, default=None)
    opt_out = Column(Boolean, nullable=False, default=False)
    # An integer that organizes the users by the number of
    # badges they have ever been awarded.  A value of None
    # indicates that they have not been ranked yet at all.
    rank = Column(Integer, default=None)

    def __repr__(self):
        return "<Person: '%s <%s>'" % (self.nickname, self.email)

    @property
    def gravatar_link(self):
        d, s = "mm", 24
        hash = hashlib.md5(self.email).hexdigest()
        url = "http://www.gravatar.com/avatar/%s?s=%i&d=%s" % (hash, s, d)
        return url

    def __unicode__(self):
        return str(self.email)

    __str__ = __unicode__

    def __json__(self):
        return dict(
            email=self.email,
            id=self.id,
            nickname=self.nickname,
            website=self.website,
            bio=self.bio,
            rank=self.rank,
        )


def invitation_id_default(context):
    return hashlib.md5(salt_default(context).encode("utf-8")).hexdigest()


class Invitation(DeclarativeBase):
    """ This is a temporary invitation to receive a badge.

    The idea is that a user can create a "You made my day" badge, and
    then award it to another user.  However, instead of just directly
    associating the righthand user with the badge, we "invite" them
    to accept it.

    """

    __tablename__ = "invitations"
    id = Column(
        Unicode(32), primary_key=True, unique=True, default=invitation_id_default
    )
    created_on = Column(DateTime, nullable=False)
    expires_on = Column(DateTime, nullable=False)
    badge_id = Column(Unicode(128), ForeignKey("badges.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("persons.id"), nullable=False)

    @property
    def expired(self):
        return datetime.datetime.utcnow() > self.expires_on

    @property
    def expires_on_relative(self):
        return arrow.get(self.expires_on).humanize()


class Authorization(DeclarativeBase):
    __tablename__ = "authorizations"
    id = Column(Integer, primary_key=True)
    badge_id = Column(Unicode(128), ForeignKey("badges.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)


def recipient_default(context):
    Session = sessionmaker(context.engine)()
    person_id = context.current_parameters["person_id"]
    person = Session.query(Person).filter_by(id=person_id).one()

    return hashlib.sha256(
        (person.email + context.current_parameters["salt"]).encode("utf-8")
    ).hexdigest()


def salt_default(context):
    return str(uuid.uuid4())


def assertion_id_default(context):
    person_id = context.current_parameters["person_id"]
    badge_id = context.current_parameters["badge_id"]
    return "%s -> %r" % (badge_id, person_id)


class Assertion(DeclarativeBase):
    __tablename__ = "assertions"
    id = Column(
        Unicode(128), primary_key=True, unique=True, default=assertion_id_default
    )
    badge_id = Column(Unicode(128), ForeignKey("badges.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    salt = Column(Unicode(128), nullable=False, default=salt_default)
    issued_on = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # An optional link back to the event that warranted the award
    issued_for = Column(Unicode(256))

    recipient = Column(Unicode(256), nullable=False, default=recipient_default)

    def __unicode__(self):
        return str(self.badge) + "<->" + str(self.person)

    __str__ = __unicode__

    @property
    def _recipient(self):
        return "sha256${0}".format(self.recipient)

    def __json__(self):
        result = dict(
            recipient=self._recipient, salt=self.salt, badge=self.badge.__json__()
        )
        # Eliminate this check since I made issued_on not nullable?
        if self.issued_on:
            result["issued_on"] = self.issued_on.strftime("%Y-%m-%d")
        return result

    def __getitem__(self, key):
        if key not in ("pygments", "delete"):
            raise KeyError
        return getattr(self, "__{0}__".format(key))()

    def __delete__(self):
        return lambda: DBSession.delete(self)

    def __pygments__(self):
        html_args = {"full": False}
        pretty_encoder = simplejson.encoder.JSONEncoder(indent=2)
        html = pygments.highlight(
            pretty_encoder.encode(self.__json__()),
            pygments.lexers.JavascriptLexer(),
            pygments.formatters.HtmlFormatter(**html_args),
        ).strip()
        return html
