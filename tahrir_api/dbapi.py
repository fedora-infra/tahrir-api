# -*- coding: utf-8 -*-
# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: API For interacting with the Tahrir database

from __future__ import unicode_literals

from utils import autocommit
from model import Badge, Invitation, Issuer, Assertion, Person
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import (
    datetime,
    timedelta,
)


class TahrirDatabase(object):
    """
    Class for talking to the Tahrir database
    It handles adding information necessary to issue open badges

    Pass one or the other of the two parameters, but not both.

    :type dburi: str
    :param dburi: the sqlalchemy database URI

    :type session: SQLAlchemy session object
    :param session: an already configured session object.
    """

    def __init__(self, dburi=None, session=None, autocommit=True):
        if not dburi and not session:
            raise ValueError("You must provide either 'dburi' or 'session'")

        if dburi and session:
            raise ValueError("Provide only one, either 'dburi' or 'session'")

        self.autocommit = autocommit
        self.session = session

        if dburi:
            self.session_maker = sessionmaker(bind=create_engine(dburi))
            self.session = scoped_session(self.session_maker)

    def badge_exists(self, badge_id):
        """
        Check to see if this badge already exists in the database

        :type badge_id: str
        :param badge_id: The ID of a Badge
        """

        return self.session.query(Badge).filter(
                func.lower(Badge.id) == func.lower(badge_id)).count() != 0

    def get_badge(self, badge_id):
        """
        Return the badge with the given ID

        :type badge_id: str
        :param badge_id: The ID of the badge to return
        """

        if self.badge_exists(badge_id):
            return self.session.query(Badge).filter(
                    func.lower(Badge.id) == func.lower(badge_id)).one()
        return None

    def get_badges_from_tags(self, tags, match_all=False):
        """
        Return badges matching tags.

        :type tags: list
        :param tags: A list of string badge tags

        :type match_all: boolean
        :param match_all: Returned badges must have all tags in list
        """

        badges = list()

        if match_all:
            # Return badges matching all tags
            # ... by doing argument-expansion on a list comprehension
            badges.extend(self.session.query(Badge).filter(and_(*[
                func.lower(Badge.tags).contains(str(tag + ',').lower())
                for tag in tags])))
        else:
            # Return badges matching any of the tags
            for tag in tags:
                badges.extend(self.session.query(Badge).filter(
                              func.lower(Badge.tags).contains(
                              str(tag + ',').lower())).all())

        # Eliminate any duplicates.
        unique_badges = list()
        for badge in badges:
            if badge not in unique_badges:
                unique_badges.append(badge)

        return unique_badges

    def get_all_badges(self):
        """
        Get all badges in the db.
        """

        return self.session.query(Badge)

    @autocommit
    def delete_badge(self, badge_id):
        """
        Delete a badge from the database

        :type badge_id: str
        :param badge_id: ID of the badge to delete
        """

        if self.badge_exists(badge_id):
            to_delete = self.session.query(Badge).filter_by(id=badge_id).one()
            self.session.delete(to_delete)
            self.session.flush()
            return badge_id
        return False

    @autocommit
    def add_badge(self, name, image, desc, criteria, issuer_id,
                  tags=None, badge_id=None):
        """
        Add a new badge to the database

        :type name: str
        :param name: Name of the Badge

        :type image: str
        :param image: URL of the image for this Badge

        :type criteria: str
        :param criteria: The criteria of this Badge

        :type issuer_id: int
        :param issuer_id: The ID of the issuer who issues this Badge

        :type tags: str
        :param tags: Comma-delimited list of badge tags.
        """

        if not badge_id:
            badge_id = name.lower().replace(" ", "-")

            bad = ['"', "'", '(', ')', '*', '&']
            replacements = dict(zip(bad, [''] * len(bad)))

            for a, b in replacements.items():
                badge_id = badge_id.replace(a, b)

        if not self.badge_exists(badge_id):
            # Make sure the tags string has a trailing
            # comma at the end. The tags view in Tahrir
            # depends on that comma when matching all
            # tags.
            if tags and not tags.endswith(','):
                tags = tags + ','

            # Actually add the badge.
            new_badge = Badge(id=badge_id,
                              name=name,
                              image=image,
                              description=desc,
                              criteria=criteria,
                              issuer_id=issuer_id,
                              tags=tags)
            self.session.add(new_badge)
            self.session.flush()
        return badge_id

    def person_exists(self, email=None, id=None, nickname=None):
        """
        Check if a Person with this email is stored in the database

        :type email: str
        :param email: An email address to search the database for

        :type id: str
        :param id: A user id to search for.

        :type nickname: str
        :param nickname: A nickname to search for.
        """

        query = self.session.query(Person)
        if email:
            return query.filter(
                    func.lower(Person.email) == func.lower(email)).count() != 0
        elif id:
            return query.filter_by(id=id).count() != 0
        elif nickname:
            return query.filter(
                    func.lower(Person.nickname) == func.lower(
                             nickname)).count() != 0
        else:
            return False

    def person_opted_out(self, email=None, id=None, nickname=None):
        """ Returns true if a given person has opted out of tahrir. """

        person = self.get_person(email, id, nickname)

        # If they don't exist, then they haven't opted out.
        if not person:
            return False

        # Otherwise, return whatever value they have in the DB.
        return person.opt_out

    def get_all_persons(self):
        """
        Gets all the persons in the db.
        """

        return self.session.query(Person)

    def get_person_email(self, person_id):
        """
        Convience function to retrieve a person email from an id.

        I am so sorry that I had to write this.
        It is easier than rewriting all of the get_person and
        person_exists methods to take ids for now.
        Eventaully, I will get around to fully refactoring
        this API.

        This was written after get_person etc., and at some point we really
        should make all these methods uniform (either get_x and
        get_x_by_email or get_x and get_x_by_id).

        :type person_id: str
        :param person_id: The email of a Person in the database.
        """

        if self.person_exists(id=person_id):
            return self.session.query(Person).filter(
                    func.lower(Person.id) == func.lower(person_id)).one().email
        return None

    def get_person(self, person_email=None, id=None, nickname=None):
        """
        Convenience function to retrieve a person object from an email,
        id, or nickname.

        :type person_email: str
        :param person_email: The email address of a Person in the database

        :type id: str
        :param id: The id of a Person in the database

        :type nickname: str
        :param nickname: The nickname of a Person in the database
        """

        query = self.session.query(Person)

        if person_email and self.person_exists(email=person_email):
            return query.filter(
                    func.lower(Person.email) == \
                            func.lower(person_email)).one()
        elif id and self.person_exists(id=id):
            return query.filter_by(id=id).one()
        elif nickname and self.person_exists(nickname=nickname):
            return query.filter(
                    func.lower(Person.nickname) == \
                            func.lower(nickname)).one()
        else:
            return None

    @autocommit
    def delete_person(self, person_email):
        """
        Delete a person with the given email

        :type person_email: str
        :param person_email: Email of the person to delete
        """

        if self.person_exists(email=person_email):
            self.session.delete(self.get_person(person_email))
            self.session.flush()
            return person_email
        return False

    @autocommit
    def add_person(self, email, nickname=None,
                   website=None, bio=None):
        """
        Add a new Person to the database

        :type email: str
        :param email: This Person's email address

        :type nickname: str
        :param nickname: This Person's nickname

        :type website: str
        :param website: This Person's website

        :type website: str
        :param bio: This Person's bio
        """

        if not self.person_exists(email=email):

            # If no nickname is specified, just use the first bit of their
            # email as a convenient default.
            if not nickname:
                nickname = email.split('@')[0]

            new_person = Person(email=email, nickname=nickname,
                                website=website, bio=bio)
            self.session.add(new_person)
            self.session.flush()

            return email
        return False

    def issuer_exists(self, origin, name):
        """
        Check to see if an issuer with this ID is in the database

        :type issuer_id: int
        :param issuer_id: The unique ID of this issuer
        """

        return self.session.query(Issuer)\
                .filter_by(origin=origin, name=name).count() != 0

    @autocommit
    def add_invitation(self, badge_id, created_on=None, expires_on=None,
                       created_by=None):
        """
        Add a new invitation to the database

        :type badge_id: str
        :param badge_id: A badge ID

        :type created_on: datetime.datetime
        :param created_on: When this invitation was created.

        :type expires_on: datetime.datetime
        :param expires_on: When this invitation expires.

        :type created_by: int
        :param created_by: User ID of creator

        """

        if not self.badge_exists(badge_id):
            raise ValueError("No such badge %r" % badge_id)

        created_on = created_on or datetime.now()
        expires_on = expires_on or (created_on + timedelta(hours=1))
        created_by = created_by or "1"  # This should be fine

        invitation = Invitation(
            created_on=created_on,
            expires_on=expires_on,
            badge_id=badge_id,
            created_by=created_by,
        )
        self.session.add(invitation)
        self.session.flush()
        return invitation.id

    def invitation_exists(self, invitation_id):
        """
        Check to see if an invitation exists with this ID.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation
        """

        return self.session.query(Invitation)\
                .filter_by(id=invitation_id).count() != 0

    def get_all_invitations(self):
        """
        Get all invitations in the db.
        """

        return self.session.query(Invitation)

    def get_invitation(self, invitation_id):
        """
        Get invitation by an invitation id.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation
        """

        if self.invitation_exists(invitation_id):
            return self.session.query(Invitation)\
                    .filter_by(id=invitation_id).one()
        else:
            return False

    def get_invitations(self, person_id):
        """
        Get invitations created by a particular person.

        :type issuer_id: str
        :param issuer_id: The person ID for which inviations
                          will be retrieved.
        """

        return self.session.query(Invitation)\
                .filter_by(created_by=person_id).all()

    def get_issuer(self, issuer_id):
        """
        Return the issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to return
        """
        query = self.session.query(Issuer).filter_by(id=issuer_id)
        if query.count() > 0:
            return query.one()
        return None

    @autocommit
    def delete_issuer(self, issuer_id):
        """
        Delete an issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to be delete
        """

        query = self.session.query(Issuer).filter_by(id=issuer_id)
        if query.count() > 0:
            to_delete = query.one()
            self.session.delete(to_delete)
            self.session.flush()
            return issuer_id
        return False

    @autocommit
    def add_issuer(self, origin, name, org, contact):
        """
        Add a new issuer to the Database

        :type origin: str
        :param origin: This issuers origin

        :type name: str
        :param name: Name of this issuer

        :type org: str
        :param org: The org of this issuer

        :type contact: str
        :param contact: The Contact email for this issuer
        """

        if not self.issuer_exists(origin, name):
            new_issuer = Issuer(
                origin=origin,
                name=name,
                org=org,
                contact=contact,
            )
            self.session.add(new_issuer)
            self.session.flush()
            return new_issuer.id

        return self.session.query(Issuer)\
            .filter_by(name=name, origin=origin).one().id

    def get_all_issuers(self):
        """
        Get all issuers in the db.
        """

        return self.session.query(Issuer)

    def get_all_assertions(self):
        """
        Get all assertions in the db.
        """

        return self.session.query(Assertion)

    def get_assertions_by_email(self, person_email):
        """
        Get all assertions attached to the given email

        :type person_email: str
        :param person_email: Email of the person to get assertions for
        """

        if self.person_exists(email=person_email):
            person_id = self.session.query(Person).filter_by(
                    email=person_email).one().id
            return self.session.query(Assertion).filter_by(
                    person_id=person_id).all()
        else:
            return False

    def get_assertions_by_badge(self, badge_id):
        """
        Get all assertions of a particular badge.

        :type badge_id: str
        :param badge_id: Badge id to get assertions for.
        """

        if self.badge_exists(badge_id):
            return self.session.query(Assertion).filter(
                    func.lower(Assertion.badge_id) ==\
                            func.lower(badge_id)).all()
        else:
            return False

    def assertion_exists(self, badge_id, email):
        """
        Check if an assertion exists in the database

        :type badge_id: str
        :param badge_id: ID of the badge

        :type email: str
        :param email: users email
        """

        person = self.get_person(email)

        if not person:
            return False

        return self.session.query(Assertion).filter_by(
                person_id=person.id, badge_id=badge_id).count() != 0

    @autocommit
    def add_assertion(self, badge_id, person_email, issued_on):
        """
        Add an assertion (award a badge) to the database

        :type badge_id: str
        :param badge_id: ID of the badge to be issued

        :type person_email: str
        :param person_email: Email of the Person to issue the badge to

        :type issued_on: DateTime
        :param issued_on: DateTime object holding the date the badge was issued
        on
        """

        if issued_on is None:
            issued_on = datetime.now()

        if self.person_exists(email=person_email) and \
           self.badge_exists(badge_id):

            new_assertion = Assertion(badge_id=badge_id,
                                      person_id=self.get_person(
                                          person_email).id,
                                      issued_on=issued_on)
            self.session.add(new_assertion)
            self.session.flush()
            return (person_email, badge_id)
        return False
