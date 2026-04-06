# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: Base manager class for Tahrir database modules


class BaseManager:
    """Base class for all database managers"""

    def __init__(self, session, db_instance=None):
        self.session = session
        self._db = db_instance
        self.autocommit = False

    def _get_db(self):
        """Get the main database instance for cross-references"""
        return self._db

    # Cross-reference properties
    @property
    def teams(self):
        return self._get_db().teams if self._get_db() else None

    @property
    def series(self):
        return self._get_db().series if self._get_db() else None

    @property
    def milestones(self):
        return self._get_db().milestones if self._get_db() else None

    @property
    def badges(self):
        return self._get_db().badges if self._get_db() else None

    @property
    def persons(self):
        return self._get_db().persons if self._get_db() else None

    @property
    def issuers(self):
        return self._get_db().issuers if self._get_db() else None

    @property
    def invitations(self):
        return self._get_db().invitations if self._get_db() else None

    @property
    def assertions(self):
        return self._get_db().assertions if self._get_db() else None

    @property
    def authorizations(self):
        return self._get_db().authorizations if self._get_db() else None

    @property
    def ranking(self):
        return self._get_db().ranking if self._get_db() else None
