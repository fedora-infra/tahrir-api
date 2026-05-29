# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: API For interacting with the Tahrir database

from .db import (
    AssertionMethod,
    AuthorizationMethod,
    BadgeMethod,
    InvitationMethod,
    IssuerMethod,
    LeaderboardMethod,
    MilestoneMethod,
    PersonMethod,
    RarityMethod,
    SeriesMethod,
    TagMethod,
    TeamMethod,
)
from .utils import get_db_manager_from_uri


class TahrirDatabase(
    TagMethod,
    BadgeMethod,
    PersonMethod,
    RarityMethod,
    IssuerMethod,
    AssertionMethod,
    AuthorizationMethod,
    InvitationMethod,
    TeamMethod,
    SeriesMethod,
    MilestoneMethod,
    LeaderboardMethod,
):
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
