# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: API For interacting with the Tahrir database

import importlib.resources
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, not_, text
from sqlalchemy_helpers import DatabaseManager
from tahrir_messages import BadgeAwardV1, PersonLoginFirstV1, PersonRankAdvanceV1

from .model import (
    Assertion,
    Authorization,
    Badge,
    Invitation,
    Issuer,
    Milestone,
    Person,
    Series,
    Team,
)
from .utils import autocommit, convert_name_to_id


class TahrirDatabase:
    """
    Class for talking to the Tahrir database
    It handles adding information necessary to issue open badges

    Pass one or the other of the two parameters, but not both.

    :type dburi: str
    :param dburi: the sqlalchemy database URI

    :type session: SQLAlchemy session object
    :param session: an already configured session object.
    """

    def __init__(self, dburi=None, session=None, autocommit=True, notification_callback=None):
        if not dburi and not session:
            raise ValueError("You must provide either 'dburi' or 'session'")

        if dburi and session:
            raise ValueError("Provide only one, either 'dburi' or 'session'")

        self.autocommit = autocommit

        if dburi:
            with importlib.resources.as_file(
                importlib.resources.files("tahrir_api").joinpath("migrations")
            ) as alembic_path:
                self.db_mgr = DatabaseManager(dburi, alembic_path.as_posix())
            self.session = self.db_mgr.Session()
        else:
            self.session = session

        self.notification_callback = notification_callback

    def team_exists(self, team_id):
        """
        Check to see if this team already exists in the database

        :type team_id: str
        :param team_id: The ID of a Team
        """

        return (
            self.session.query(Team).filter(func.lower(Team.id) == func.lower(team_id)).count() != 0
        )

    def get_team(self, team_id):
        """
        Return the team with the given ID

        :type team_id: str
        :param team_id: The ID of the team to return
        """

        if self.team_exists(team_id):
            return (
                self.session.query(Team).filter(func.lower(Team.id) == func.lower(team_id)).first()
            )
        return None

    @autocommit
    def create_team(self, name, team_id=None):
        """
        Adds a new team to the database

        :type name: str
        :param name: Name of the team
        :type team_id: int
        :param team_id: Id of the team
        """

        if not team_id:
            team_id = convert_name_to_id(name)

        if not self.team_exists(team_id):
            new_team = Team(id=team_id, name=name)

            self.session.add(new_team)
            self.session.flush()
        return team_id

    def series_exists(self, series_id):
        """
        Check to see if this series already exists in the database

        :type series_id: str
        :param series_id: The ID of a Series
        """

        return (
            self.session.query(Series)
            .filter(func.lower(Series.id) == func.lower(series_id))
            .count()
            != 0
        )

    def get_series(self, series_id):
        """
        Return the series with the given ID

        :type series_id: str
        :param series_id: The ID of the series to return
        """

        if self.series_exists(series_id):
            return (
                self.session.query(Series)
                .filter(func.lower(Series.id) == func.lower(series_id))
                .one()
            )
        return None

    def get_series_from_team(self, team_id):
        """
        Return the series related to a given team ID

        :type team_id: str
        :param team_id: The ID of the team
        """
        if self.team_exists(team_id):
            return self.session.query(Series).filter(Series.team_id == team_id).all()

    @autocommit
    def create_series(self, name, desc, team_id, tags=None, series_id=None):
        """
        Adds a new series to the database

        :type name: str
        :param name: Name of the Series

        :type desc: str
        :param desc: Description of the Series

        :type team_id: str
        :param team_id: Team Id to which this Series belongs to

        :type tags: str
        :param tags: Tags for a Series

        :type series_id: str
        :param series_id: ID of the Series
        """

        if not series_id:
            series_id = convert_name_to_id(name)

        if not self.series_exists(series_id):
            new_series = Series(
                id=series_id, name=name, description=desc, tags=tags, team_id=team_id
            )

            self.session.add(new_series)
            self.session.flush()
        return series_id

    def get_all_series(self):
        """
        Get all series in the db.
        """

        return self.session.query(Series)

    def milestone_exists(self, milestone_id):
        """
        Check to see if this milestone already exists in the database

        :type milestone_id: str
        :param milestone_id: The ID of a Milestone
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id).count() != 0

    def milestone_exists_for_badge_series(self, badge_id, series_id):
        """
        Check if the milestone with the given series and badge id exists

        :type badge_id: str
        :param badge_id: The ID of the badge

        :type series_id: str
        :param series_id: The ID of the series
        """
        return self.get_milestone_from_badge_series(badge_id, series_id).count() != 0

    def get_milestone_from_badge_series(self, badge_id, series_id):
        """
        Return the milestone with the given series and badge id

        :type badge_id: str
        :param badge_id: The ID of the badge

        :type series_id: str
        :param series_id: The ID of the series
        """
        return self.session.query(Milestone).filter(
            and_(
                Milestone.series_id == func.lower(series_id),
                Milestone.badge_id == func.lower(badge_id),
            )
        )

    def get_milestone(self, milestone_id):
        """
        Return the matching milestone from the database

        :type milestone_id: str
        :param milestone_id: The ID of a Milestone
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id)

    def get_all_milestones(self, series_id):
        """
        Returns all the milestones for the series

        :type series_id: str
        :param series_id: The id of the Series
        """
        return self.session.query(Milestone).filter(Milestone.series_id == series_id).all()

    @autocommit
    def create_milestone(self, position, badge_id, series_id):
        """
        Adds a new milestone to the database

        :type name: int
        :param name: position of the milestone in the series

        :type badge_id: str
        :param badge_id: Badge ID for the Milestone

        :type series_id: str
        :param series_id: ID of the Series
        """
        milestone = self.get_milestone_from_badge_series(badge_id, series_id).first()
        if not milestone:
            milestone = Milestone(position=position, badge_id=badge_id, series_id=series_id)

            self.session.add(milestone)
            self.session.flush()
        milestone_id = milestone.id

        return milestone_id

    def get_milestone_from_series_ids(self, series_ids):
        """
        Return list of milestones for the list of series ids

        :type series: list
        :param series: list of series ids
        """
        milestones = self.session.query(Milestone).filter(Milestone.series_id.in_(series_ids)).all()

        seen = set()
        unique_milestones = []

        for milestone in milestones:
            milestone_meta = (milestone.series_id, milestone.id)
            if milestone_meta not in seen:
                seen.add(milestone_meta)
                unique_milestones.append(milestone)

        return unique_milestones

    def get_badges_from_team(self, team_id):
        """
        Returns all the badges related to a team

        :type team_id: str
        :param team_id: id of the team
        """
        if self.team_exists(team_id):
            series = self.get_series_from_team(team_id)
            series_ids = [elem.id for elem in series]

            milestones = self.get_milestone_from_series_ids(series_ids)
            badge_ids = list(set([milestone.badge_id for milestone in milestones]))

            badges = self.get_badges(badge_ids)
            return badges
        return None

    def badge_exists(self, badge_id):
        """
        Check to see if this badge already exists in the database

        :type badge_id: str
        :param badge_id: The ID of a Badge
        """

        return (
            self.session.query(Badge).filter(func.lower(Badge.id) == func.lower(badge_id)).count()
            != 0
        )

    def get_badge(self, badge_id):
        """
        Return the badge with the given ID

        :type badge_id: str
        :param badge_id: The ID of the badge to return
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Badge).filter(func.lower(Badge.id) == func.lower(badge_id)).one()
            )
        return None

    def get_badges(self, badge_ids):
        """
        Return the badges with the given IDs

        :type badge_ids: list
        :param badge_ids: The list of badge IDs
        """
        badges = self.session.query(Badge).filter(Badge.id.in_(badge_ids)).all()

        return badges

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
            badges.extend(
                self.session.query(Badge).filter(
                    and_(*[func.lower(Badge.tags).contains(str(tag + ",").lower()) for tag in tags])
                )
            )
        else:
            # Return badges matching any of the tags
            for tag in tags:
                badges.extend(
                    self.session.query(Badge)
                    .filter(func.lower(Badge.tags).contains(str(tag + ",").lower()))
                    .all()
                )

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
    def add_badge(self, name, image, desc, criteria, issuer_id, tags=None, badge_id=None):
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
            badge_id = convert_name_to_id(name)

        if not self.badge_exists(badge_id):
            # Make sure the tags string has a trailing
            # comma at the end. The tags view in Tahrir
            # depends on that comma when matching all
            # tags.
            if tags and not tags.endswith(","):
                tags = tags + ","

            # Actually add the badge.
            new_badge = Badge(
                id=badge_id,
                name=name,
                image=image,
                description=desc,
                criteria=criteria,
                issuer_id=issuer_id,
                tags=tags,
            )
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
            return query.filter(func.lower(Person.email) == func.lower(email)).count() != 0
        elif id:
            return query.filter_by(id=id).count() != 0
        elif nickname:
            return query.filter(func.lower(Person.nickname) == func.lower(nickname)).count() != 0
        else:
            return False

    def person_opted_out(self, email=None, id=None, nickname=None):
        """Returns true if a given person has opted out of tahrir."""

        person = self.get_person(email, id, nickname)

        # If they don't exist, then they haven't opted out.
        if not person:
            return False

        # Otherwise, return whatever value they have in the DB.
        return person.opt_out

    def get_all_persons(self, include_opted_out=False):
        """
        Gets all the persons in the db.
        """

        query = self.session.query(Person)
        if not include_opted_out:
            query = query.filter(not_(Person.opt_out))
        return query

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
            return (
                self.session.query(Person)
                .filter(func.lower(Person.id) == func.lower(person_id))
                .one()
                .email
            )
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
            return query.filter(func.lower(Person.email) == func.lower(person_email)).one()
        elif id and self.person_exists(id=id):
            return query.filter_by(id=id).one()
        elif nickname and self.person_exists(nickname=nickname):
            return query.filter(func.lower(Person.nickname) == func.lower(nickname)).one()
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
    def add_person(self, email, nickname=None, website=None, bio=None, avatar=None):
        """
        Add a new Person to the database

        :type email: str
        :param email: This Person's email address

        :type nickname: str
        :param nickname: This Person's nickname

        :type website: str
        :param website: This Person's website

        :type bio: str
        :param bio: This Person's bio

        :type avatar: str
        :param avatar: This Person's avatar
        """

        if not self.person_exists(email=email):
            # If no nickname is specified, just use the first bit of their
            # email as a convenient default.
            if not nickname:
                nickname = email.split("@")[0]

            new_person = Person(
                email=email, nickname=nickname, website=website, bio=bio, _avatar=avatar
            )
            self.session.add(new_person)
            self.session.flush()

            return email
        return False

    @autocommit
    def note_login(self, person_email=None, id=None, nickname=None):
        """Make a note that a person has logged in."""

        person = self.get_person(person_email, id, nickname)

        # If this is the first time they have ever logged in, optionally
        # publish a notification about the event.
        if not person.last_login and self.notification_callback:
            body = dict(user=dict(username=person.nickname, badges_user_id=person.id))
            self.notification_callback(PersonLoginFirstV1(body=body))

        # Finally, update the field.
        person.last_login = datetime.now(timezone.utc)

    def issuer_exists(self, origin, name):
        """
        Check to see if an issuer with this ID is in the database

        :type issuer_id: int
        :param issuer_id: The unique ID of this issuer
        """

        return self.session.query(Issuer).filter_by(origin=origin, name=name).count() != 0

    @autocommit
    def add_invitation(self, badge_id, created_on=None, expires_on=None, created_by_email=None):
        """
        Add a new invitation to the database

        :type badge_id: str
        :param badge_id: A badge ID

        :type created_on: datetime.datetime
        :param created_on: When this invitation was created.

        :type expires_on: datetime.datetime
        :param expires_on: When this invitation expires.

        :type created_by: str
        :param created_by_email: User email of creator

        """

        if not self.badge_exists(badge_id):
            raise ValueError(f"No such badge {badge_id!r}")

        created_on = created_on or datetime.now(timezone.utc)
        expires_on = expires_on or (created_on + timedelta(hours=1))
        if self.person_exists(email=created_by_email):
            created_by = self.get_person(created_by_email).id
        else:
            created_by = self.session.query(Person).first().id

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

        return self.session.query(Invitation).filter_by(id=invitation_id).count() != 0

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
            return self.session.query(Invitation).filter_by(id=invitation_id).one()
        else:
            return False

    def get_invitations(self, person_id):
        """
        Get invitations created by a particular person.

        :type issuer_id: str
        :param issuer_id: The person ID for which inviations
                          will be retrieved.
        """

        return self.session.query(Invitation).filter_by(created_by=person_id).all()

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
            new_issuer = Issuer(origin=origin, name=name, org=org, contact=contact)
            self.session.add(new_issuer)
            self.session.flush()
            return new_issuer.id

        return self.session.query(Issuer).filter_by(name=name, origin=origin).one().id

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
            person_id = self.session.query(Person).filter_by(email=person_email).one().id
            return self.session.query(Assertion).filter_by(person_id=person_id).all()
        else:
            return False

    def get_assertions_by_badge(self, badge_id):
        """
        Get all assertions of a particular badge.

        :type badge_id: str
        :param badge_id: Badge id to get assertions for.
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Assertion)
                .filter(func.lower(Assertion.badge_id) == func.lower(badge_id))
                .all()
            )
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

        return (
            self.session.query(Assertion).filter_by(person_id=person.id, badge_id=badge_id).count()
            != 0
        )

    def authorization_exists(self, badge_id, email):
        """
        Check if an authorization exists in the database

        :type badge_id: str
        :param badge_id: ID of the badge

        :type email: str
        :param email: user's email
        """

        person = self.get_person(email)

        if not person:
            return False

        return (
            self.session.query(Authorization)
            .filter_by(person_id=person.id, badge_id=badge_id)
            .count()
            != 0
        )

    @autocommit
    def add_authorization(self, badge_id, person_email):
        """
        Add an authorization (allow someone to admin a certain badge)

        :type badge_id: str
        :param badge_id: ID of the badge

        :type person_email: str
        :param person_email: Email of the Person grant rights to
        """

        if self.person_exists(email=person_email) and self.badge_exists(badge_id):
            person = self.get_person(person_email)

            new_authz = Authorization(badge_id=badge_id, person_id=person.id)
            self.session.add(new_authz)
            self.session.flush()

            return (person_email, badge_id)

        return False

    @autocommit
    def add_assertion(self, badge_id, person_email, issued_on, issued_for=None):
        """
        Add an assertion (award a badge) to the database

        :type badge_id: str
        :param badge_id: ID of the badge to be issued

        :type person_email: str
        :param person_email: Email of the Person to issue the badge to

        :type issued_on: DateTime
        :param issued_on: DateTime object holding the date the badge was issued
        on

        :type issued_for: str
        :param issued_for: An optional link back to the warranting event
        """

        if issued_on is None:
            issued_on = datetime.now(timezone.utc)

        if self.person_exists(email=person_email) and self.badge_exists(badge_id):
            badge = self.get_badge(badge_id)
            person = self.get_person(person_email)
            old_rank = person.rank

            new_assertion = Assertion(
                badge_id=badge_id,
                person_id=person.id,
                issued_on=issued_on,
                issued_for=issued_for,
            )
            self.session.add(new_assertion)
            self.session.flush()

            if self.notification_callback:
                body = dict(
                    badge=dict(
                        name=badge.name,
                        description=badge.description,
                        image_url=badge.image,
                        badge_id=badge_id,
                    ),
                    user=dict(username=person.nickname, badges_user_id=person.id),
                )
                self.notification_callback(BadgeAwardV1(body=body))

            self._adjust_ranks(person, old_rank)

            return person_email, badge_id

        return False

    def _adjust_ranks(self, person, old_rank):
        """Given a person model object and the 'old' rank of that person,
        adjust the ranks of all persons between the 'old' rank and the present
        rank of the given person.

        This is a utility function typically called when a person is awarded a
        new badge, and their rank advances.  Since we cache rank in the
        database, we want to also decrement the rank of all persons that the
        given person is "passing" on the all-time leaderboard.
        """

        # Build a dict of Persons to some freshly calculated rank info.
        leaderboard = self._make_leaderboard()

        # Recalculate rank in all cases, otherwise "overtaking" won't work
        # anymore (with rank being shared, a new badge won't change a person's
        # own position, but needs to demote the rest).

        # Otherwise, take our calculations and commit them to the db.
        for _person, data in leaderboard.items():
            _person.rank = data["rank"]

        self.session.flush()

        body = dict(person=person.as_dict(), old_rank=old_rank)
        if self.notification_callback:
            self.notification_callback(PersonRankAdvanceV1(body=body))

    def _make_leaderboard(self, start=None, stop=None):
        """Produce a dict mapping persons to information about
        the number of badges they have been awarded and their
        rank, freshly calculated.  This is relatively expensive.

        The 'start' and 'stop' parameters are optional datetime objects.
        If specified, the leaderboard will be calculated from badges that were
        awarded only in the time period between 'start' and 'stop'.  Passing
        only one of 'start' or 'stop' is meaningless -- the other value will be
        discarded.  Passing neither value will return the "all time"
        leaderboard.

        People with no badges in the specified period are expected to have a
        null/None rank.  They will be absent from the returned leaderboard
        dict.

        Ricky Elrod originally contributed this to tahrir.
        Moved here by Ralph Bean.
        """

        leaderboard = self.session.query(
            Person, func.count(Person.assertions).label("count_1")
        ).join(Assertion)

        if start and stop:
            leaderboard = leaderboard.filter(Assertion.issued_on >= start).filter(
                Assertion.issued_on <= stop
            )

        leaderboard = (
            leaderboard.order_by(text("count_1 desc"))
            .filter(not_(Person.opt_out))
            .group_by(Person)
            .all()
        )

        # Hackishly, but relatively cheaply get the rank of all users.
        # This is:
        # { <person object>:
        #   {
        #     'badges': <number of badges they have>,
        #     'rank': <their global rank>
        #   }
        # }
        #
        # Tweaked so that users with the same amount of badges share rank.

        user_to_rank = OrderedDict()

        prev_rank, prev_badges = None, None

        for idx, data in enumerate(leaderboard):
            user, badges = data[0:2]
            if badges == prev_badges:
                # same amount of badges -> same rank
                rank = prev_rank
            else:
                prev_rank = rank = idx + 1
                prev_badges = badges
            user_to_rank[user] = {"badges": badges, "rank": rank}

        return user_to_rank
