# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: API For interacting with the Tahrir database - Modular Version

from .database.managers import (
    AssertionManager,
    AuthorizationManager,
    BadgeManager,
    InvitationManager,
    IssuerManager,
    MilestoneManager,
    PersonManager,
    RankingManager,
    SeriesManager,
    TeamManager,
)
from .utils import get_db_manager_from_uri


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
            db_mgr = get_db_manager_from_uri(dburi)
            self.session = db_mgr.Session()
        else:
            self.session = session

        self.notification_callback = notification_callback

        # Initialize all managers with cross-references
        self.teams = TeamManager(self.session, self)
        self.series = SeriesManager(self.session, self)
        self.milestones = MilestoneManager(self.session, self)
        self.badges = BadgeManager(self.session, self)
        self.persons = PersonManager(self.session, self)
        self.issuers = IssuerManager(self.session, self)
        self.invitations = InvitationManager(self.session, self)
        self.assertions = AssertionManager(self.session, self)
        self.authorizations = AuthorizationManager(self.session, self)
        self.ranking = RankingManager(self.session, self)

        # Set autocommit on all managers
        for manager in [
            self.teams,
            self.series,
            self.milestones,
            self.badges,
            self.issuers,
            self.invitations,
            self.authorizations,
            self.persons,
            self.assertions,
            self.ranking,
        ]:
            manager.autocommit = self.autocommit

        # Set notification_callback on managers that need it
        self.persons.notification_callback = notification_callback
        self.assertions.notification_callback = notification_callback
        self.ranking.notification_callback = notification_callback

    # Team Methods - Delegate to TeamManager
    def team_exists(self, team_id):
        """Check to see if this team already exists in the database"""
        return self.teams.team_exists(team_id)

    def get_team(self, team_id):
        """Return the team with the given ID"""
        return self.teams.get_team(team_id)

    def create_team(self, name, team_id=None):
        """Adds a new team to the database"""
        return self.teams.create_team(name, team_id)

    # Series Methods - Delegate to SeriesManager
    def series_exists(self, series_id):
        """Check to see if this series already exists in the database"""
        return self.series.series_exists(series_id)

    def get_series(self, series_id):
        """Return the series with the given ID"""
        return self.series.get_series(series_id)

    def get_series_from_team(self, team_id):
        """Return the series with the given team ID"""
        return self.series.get_series_from_team(team_id)

    def create_series(self, name, desc, team_id, tags=None, series_id=None):
        """Add a new series to the database"""
        return self.series.create_series(name, desc, team_id, tags, series_id)

    def get_all_series(self):
        """Get all series in the database"""
        return self.series.get_all_series()

    # Milestone Methods - Delegate to MilestoneManager
    def milestone_exists(self, milestone_id):
        """Check to see if this milestone already exists in the database"""
        return self.milestones.milestone_exists(milestone_id)

    def milestone_exists_for_badge_series(self, badge_id, series_id):
        """Check to see if this milestone already exists for badge series"""
        return self.milestones.milestone_exists_for_badge_series(badge_id, series_id)

    def get_milestone_from_badge_series(self, badge_id, series_id):
        """Return the milestone with the given badge and series ID"""
        return self.milestones.get_milestone_from_badge_series(badge_id, series_id)

    def get_milestone(self, milestone_id):
        """Return the milestone with the given ID"""
        return self.milestones.get_milestone(milestone_id)

    def get_all_milestones(self, series_id):
        """Get all milestones for a series"""
        return self.milestones.get_all_milestones(series_id)

    def create_milestone(self, position, badge_id, series_id):
        """Add a new milestone to the database"""
        return self.milestones.create_milestone(position, badge_id, series_id)

    def get_milestone_from_series_ids(self, series_ids):
        """Get milestones from multiple series IDs"""
        return self.milestones.get_milestone_from_series_ids(series_ids)

    # Badge Methods - Delegate to BadgeManager
    def badge_exists(self, badge_id):
        """Check to see if this badge already exists in the database"""
        return self.badges.badge_exists(badge_id)

    def get_badge(self, badge_id):
        """Return the badge with the given ID"""
        return self.badges.get_badge(badge_id)

    def get_badges(self, badge_ids):
        """Return badges with the given IDs"""
        return self.badges.get_badges(badge_ids)

    def get_badges_from_tags(self, tags, match_all=False):
        """Return badges that match the given tags"""
        return self.badges.get_badges_from_tags(tags, match_all)

    def get_all_badges(self):
        """Get all badges in the database"""
        return self.badges.get_all_badges()

    def delete_badge(self, badge_id):
        """Delete a badge from the database"""
        return self.badges.delete_badge(badge_id)

    def add_badge(self, name, image, desc, criteria, issuer_id, tags=None, badge_id=None):
        """Add a new badge to the database"""
        return self.badges.add_badge(name, image, desc, criteria, issuer_id, tags, badge_id)

    def update_badge(self, badge_id, **kwargs):
        """Update a badge in the database"""
        return self.badges.update_badge(badge_id, **kwargs)

    def get_badges_from_team(self, team_id):
        """Get all badges from a team"""
        return self.badges.get_badges_from_team(team_id)

    # Person Methods - Delegate to PersonManager
    def person_exists(self, email=None, person_id=None, nickname=None):
        """Check if a Person exists in the database"""
        return self.persons.person_exists(email, person_id, nickname)

    def person_opted_out(self, email=None, person_id=None, nickname=None):
        """Returns true if a given person has opted out of tahrir"""
        return self.persons.person_opted_out(email, person_id, nickname)

    def get_all_persons(self, include_opted_out=False):
        """Gets all the persons in the db"""
        return self.persons.get_all_persons(include_opted_out)

    def get_person_email(self, person_id):
        """Convience function to retrieve a person email from an id"""
        return self.persons.get_person_email(person_id)

    def get_person(self, person_email=None, id=None, nickname=None):
        """Convenience function to retrieve a person object from an email, id, or nickname"""
        return self.persons.get_person(person_email, id, nickname)

    def delete_person(self, person_email):
        """Delete a person with the given email"""
        return self.persons.delete_person(person_email)

    def add_person(self, email, nickname=None, website=None, bio=None, avatar=None):
        """Add a new Person to the database"""
        return self.persons.add_person(email, nickname, website, bio, avatar)

    def update_person(
        self,
        person_email=None,
        person_id=None,
        id=None,
        nickname=None,
        website=None,
        bio=None,
        avatar=None,
    ):
        """Update an existing Person's profile fields in the database"""
        return self.persons.update_person(person_email, id, nickname, website, bio, avatar)

    def note_login(self, person_email=None, person_id=None, nickname=None):
        """Make a note that a person has logged in"""
        return self.persons.note_login(person_email, person_id, nickname)

    # Issuer Methods - Delegate to IssuerManager
    def issuer_exists(self, origin, name):
        """Check to see if this issuer already exists in the database"""
        return self.issuers.issuer_exists(origin, name)

    def get_issuer(self, issuer_id):
        """Return the issuer with the given ID"""
        return self.issuers.get_issuer(issuer_id)

    def get_all_issuers(self):
        """Get all issuers in the database"""
        return self.issuers.get_all_issuers()

    def add_issuer(self, origin, name, org, contact):
        """Add a new issuer to the database"""
        return self.issuers.add_issuer(origin, name, org, contact)

    def delete_issuer(self, issuer_id):
        """Delete an issuer from the database"""
        return self.issuers.delete_issuer(issuer_id)

    # Invitation Methods - Delegate to InvitationManager
    def invitation_exists(self, invitation_id):
        """Check to see if this invitation already exists in the database"""
        return self.invitations.invitation_exists(invitation_id)

    def get_all_invitations(self):
        """Get all invitations in the database"""
        return self.invitations.get_all_invitations()

    def add_invitation(self, badge_id, created_on=None, expires_on=None, created_by_email=None):
        """Add a new invitation to the database"""
        return self.invitations.add_invitation(badge_id, created_on, expires_on, created_by_email)

    def get_invitation(self, invitation_id):
        """Get invitation by an invitation id"""
        return self.invitations.get_invitation(invitation_id)

    def expire_invitation(self, invitation_id):
        """Soft-delete an invitation by setting its expiry date to the current time"""
        return self.invitations.expire_invitation(invitation_id)

    def get_invitations(self, person_id):
        """Get invitations created by a particular person"""
        return self.invitations.get_invitations(person_id)

    # Assertion Methods - Delegate to AssertionManager
    def assertion_exists(self, badge_id, email):
        """Check to see if this assertion already exists in the database"""
        return self.assertions.assertion_exists(badge_id, email)

    def get_assertions_by_badge(self, badge_id):
        """Get all assertions of a particular badge"""
        return self.assertions.get_assertions_by_badge(badge_id)

    def get_assertions_by_email(self, person_email):
        """Return the assertions for a person with the given email"""
        return self.assertions.get_assertions_by_email(person_email)

    def get_all_assertions(self, begin=None, limit=None):
        """Get all assertions in the db, ordered by most recent first"""
        return self.assertions.get_all_assertions(begin, limit)

    def add_assertion(self, badge_id, person_email, issued_on, issued_for=None):
        """Add an assertion (award a badge) to the database"""
        return self.assertions.add_assertion(badge_id, person_email, issued_on, issued_for)

    def remove_assertion(self, badge_id, person_email):
        """Remove an assertion (revoke a badge) from the database"""
        return self.assertions.remove_assertion(badge_id, person_email)

    # Authorization Methods - Delegate to AuthorizationManager
    def authorization_exists(self, badge_id, person_email):
        """Check if an authorization exists in the database"""
        return self.authorizations.authorization_exists(badge_id, person_email)

    def add_authorization(self, badge_id, person_email):
        """Add an authorization (allow someone to admin a certain badge)"""
        return self.authorizations.add_authorization(badge_id, person_email)

    def delete_authorization(self, badge_id, person_email):
        """Delete an authorization (remove someone's admin rights for a certain badge)"""
        return self.authorizations.delete_authorization(badge_id, person_email)

    # Ranking Methods - Delegate to RankingManager
    def get_current_value(self, badge_id, person_email):
        """Return the current value for the given badge and the given person's email"""
        return self.ranking.get_current_value(badge_id, person_email)

    def set_current_value(self, badge_id, person_email, value):
        """Set the current value for the given badge and the given person's email"""
        return self.ranking.set_current_value(badge_id, person_email, value)

    def adjust_ranks(self, person):
        """Given a person model object, adjust the ranks of all persons"""
        return self.ranking.adjust_ranks(person)

    def make_leaderboard(self, start=None, stop=None):
        """
        Produce a dict mapping persons to information about
        the number of badges they have been awarded and their rank

        """
        return self.ranking.make_leaderboard(start, stop)
