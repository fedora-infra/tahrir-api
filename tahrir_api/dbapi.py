# -*- coding: utf-8 -*-
# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: API For interacting with the Tahrir database

from __future__ import unicode_literals

from model import Badge, Invitation, Issuer, Assertion, Person
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import (
    datetime,
    timedelta,
)


class TahrirDatabase(object):
    """
    Class for talking to the Tahrir database
    It handles adding information nessicary to issue open badges

    :type dburi: str
    :param dburi: the sqlalchemy database URI
    """

    def __init__(self, dburi):
        self.session_maker = sessionmaker(bind=create_engine(dburi))

    def badge_exists(self, badge_id):
        """
        Check to see if tis badge already exists in the database

        :type badge_id: str
        :param badge_id: The ID of a Badge
        """

        session = scoped_session(self.session_maker)
        return session.query(Badge).filter_by(id=badge_id).count() != 0

    def get_badge(self, badge_id):
        """
        Return the badge with the given ID

        :type badge_id: str
        :param badge_id: The ID of the badge to return
        """

        session = scoped_session(self.session_maker)
        if self.badge_exists(badge_id):
            return session.query(Badge).filter_by(id=badge_id).one()
        return None

    def delete_badge(self, badge_id):
        """
        Delete a badge from the database

        :type badge_id: str
        :param badge_id: ID of the badge to delete
        """

        session = scoped_session(self.session_maker)
        if self.badge_exists(badge_id):
            to_delete = session.query(Badge).filter_by(id=badge_id).one()
            session.delete(to_delete)
            session.commit()
            return badge_id
        return False

    def add_badge(self, name, image, desc, criteria, issuer_id):
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
        """

        session = scoped_session(self.session_maker)
        badge_id = name.lower().replace(" ", "-")

        if not self.badge_exists(badge_id):
            new_badge = Badge(name=name,
                              image=image,
                              description=desc,
                              criteria=criteria,
                              issuer_id=issuer_id)
            session.add(new_badge)
            session.commit()
            return badge_id
        return False

    def person_exists(self, email=None, id=None):
        """
        Check if a Person with this email is stored in the database

        :type person_email: str
        :param person_email: An email address to search the database for
        """

        session = scoped_session(self.session_maker)
        if email:
            return session.query(Person).filter_by(email=email).count() != 0
        elif id:
            return session.query(Person).filter_by(id=id).count() != 0
        else:
            return False

    def get_all_persons(self):
        """
        Gets all the persons in the db.
        """

        session = scoped_session(self.session_maker)
        return session.query(Person)

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

        session = scoped_session(self.session_maker)
        if self.person_exists(id=person_id):
            return session.query(Person).filter_by(
                                         id=person_id).one().email
        return None

    def get_person(self, person_email):
        """
        Convience function to retrieve a person object from an email

        :type person_email: str
        :param person_email: The email address of a Person in the database
        """

        session = scoped_session(self.session_maker)
        if self.person_exists(email=person_email):
            return session.query(Person).filter_by(email=person_email).one()
        return None

    def delete_person(self, person_email):
        """
        Delete a person with the given email

        :type person_email: str
        :param person_email: Email of the person to delete
        """

        session = scoped_session(self.session_maker)
        if self.person_exists(email=person_email):
            session.delete(self.get_person(person_email))
            session.commit()
            return person_email
        return False

    def add_person(self, email):
        """
        Add a new Person to the database

        :type person_id: int
        :param person_id: This person's unique ID

        :type person_email: str
        :param person_email: This Person's email address
        """

        session = scoped_session(self.session_maker)
        if not self.person_exists(email=email):
            new_person = Person(email=email)
            session.add(new_person)
            session.commit()
            return email
        return False

    def issuer_exists(self, origin, name):
        """
        Check to see if an issuer with this ID is in the database

        :type issuer_id: int
        :param issuer_id: The unique ID of this issuer
        """

        session = scoped_session(self.session_maker)
        return session.query(Issuer)\
                .filter_by(origin=origin, name=name).count() != 0

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

        session = scoped_session(self.session_maker)

        if not self.badge_exists(badge_id):
            raise ValueError("No such badge %r" % badge_id)

        created_on = created_on or datetime.now()
        expires_on = expires_on or (created_on + timedelta(hours=1))
        created_by = created_by or "1" # This should be fine

        invitation = Invitation(
            created_on=created_on,
            expires_on=expires_on,
            badge_id=badge_id,
            created_by=created_by,
        )
        session.add(invitation)
        session.commit()
        return invitation.id

    def invitation_exists(self, invitation_id):
        """
        Check to see if an invitation exists with this ID.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation
        """

        session = scoped_session(self.session_maker)
        return session.query(Invitation)\
                .filter_by(id=invitation_id).count() != 0

    def get_issuer(self, issuer_id):
        """
        Return the issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to return
        """
        session = scoped_session(self.session_maker)
        query = session.query(Issuer).filter_by(id=issuer_id)
        if query.count() > 0:
            return query.one()
        return None

    def delete_issuer(self, issuer_id):
        """
        Delete an issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to be delete
        """

        session = scoped_session(self.session_maker)
        query = session.query(Issuer).filter_by(id=issuer_id)
        if query.count() > 0:
            to_delete = query.one()
            session.delete(to_delete)
            session.commit()
            return issuer_id
        return False

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

        session = scoped_session(self.session_maker)
        if not self.issuer_exists(origin, name):
            new_issuer = Issuer(
                    origin=origin,
                    name=name,
                    org=org,
                    contact=contact
                    )
            session.add(new_issuer)
            session.commit()
            return new_issuer.id

        session = scoped_session(self.session_maker)
        return session.query(Issuer)\
                .filter_by(name=name, origin=origin).one().id
    
    def get_all_assertions(self):
        """
        Get all assertions in the db.
        """

        session = scoped_session(self.session_maker)
        return session.query(Assertion)

    def get_assertions_by_email(self, person_email):
        """
        Get all assertions attached to the given email

        :type person_email: str
        :param person_email: Email of the person to get assertions for
        """

        session = scoped_session(self.session_maker)
        if self.person_exists(email=person_email):
            person_id = session.query(Person).filter_by(
                                email=person_email).one().id
            return session.query(Assertion).filter_by(
                                            person_id=person_id).all()
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

        session = scoped_session(self.session_maker)
        person = self.get_person(email)
        if not person:
            return False
        return session.query(Assertion).filter_by(
                person_id=person.id, badge_id=badge_id).count() != 0

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

        session = scoped_session(self.session_maker)
        if issued_on is None:
            issued_on = datetime.now()
        if self.person_exists(email=person_email) and self.badge_exists(badge_id):
            new_assertion = Assertion(badge_id=badge_id,
                                      person_id=self.get_person(
                                          person_email).id,
                                      issued_on=issued_on)
            session.add(new_assertion)
            session.commit()
            return (person_email, badge_id)
        return False
