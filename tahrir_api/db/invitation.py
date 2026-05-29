from datetime import datetime, timedelta, timezone

from ..model import Invitation
from ..utils import autocommit


class InvitationMethod:
    """Invitation CRUD operations."""

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

        badge = self.get_badge(badge_id)
        if badge.legacy:
            raise ValueError(f"Badge {badge_id!r} is a legacy badge and cannot be invited")

        created_on = created_on or datetime.now(timezone.utc)
        expires_on = expires_on or (created_on + timedelta(hours=1))
        if not created_by_email or not self.person_exists(email=created_by_email):
            raise ValueError(f"No user with email {created_by_email!r}. Ask them to login first.")
        created_by = self.get_person(created_by_email).id

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

    @autocommit
    def expire_invitation(self, invitation_id):
        """
        Soft-delete an invitation by setting its expiry date to the current time.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation

        :returns: True if invitation was expired, False if not found
        :rtype: bool
        """
        if not self.invitation_exists(invitation_id):
            return False

        invitation = self.session.query(Invitation).filter_by(id=invitation_id).one()
        invitation.expires_on = datetime.now()
        self.session.flush()
        return True
