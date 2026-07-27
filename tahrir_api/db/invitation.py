from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Query

from ..model import Invitation
from ..utils import autocommit


class InvitationMethod:
    """Invitation CRUD operations."""

    @autocommit
    def add_invitation(
        self,
        badge_id: str,
        created_on: datetime | None = None,
        expires_on: datetime | None = None,
        created_by_email: str | None = None,
    ) -> str:
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

        badge = self.get_badge(badge_id)
        if not badge:
            raise ValueError(f"No such badge {badge_id!r}")
        if badge.legacy:
            raise ValueError(f"Badge {badge_id!r} is a legacy badge and cannot be invited")

        created_on = created_on or datetime.now(timezone.utc)
        expires_on = expires_on or (created_on + timedelta(hours=1))
        creator = self.get_person(created_by_email) if created_by_email else None
        if not creator:
            raise ValueError(f"No user with email {created_by_email!r}. Ask them to login first.")
        created_by = creator.id

        invitation = Invitation(
            created_on=created_on,
            expires_on=expires_on,
            badge_id=badge_id,
            created_by=created_by,
        )
        self.session.add(invitation)
        self.session.flush()
        return invitation.id

    def invitation_exists(self, invitation_id: str) -> bool:
        """
        Check to see if an invitation exists with this ID.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation
        """

        return self.session.query(Invitation).filter_by(id=invitation_id).count() != 0

    def get_all_invitations(self) -> Query[Invitation]:
        """
        Get all invitations in the db.
        """

        return self.session.query(Invitation)

    def get_invitation(self, invitation_id: str) -> Invitation | bool:
        """
        Get invitation by an invitation id.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation
        """

        invitation = self.session.query(Invitation).filter_by(id=invitation_id).first()
        if invitation:
            return invitation
        return False

    def get_invitations(self, person_id: int) -> list[Invitation]:
        """
        Get invitations created by a particular person.

        :type issuer_id: str
        :param issuer_id: The person ID for which inviations
                          will be retrieved.
        """

        return self.session.query(Invitation).filter_by(created_by=person_id).all()

    @autocommit
    def expire_invitation(self, invitation_id: str) -> bool:
        """
        Soft-delete an invitation by setting its expiry date to the current time.

        :type invitation_id: str
        :param invitation_id: The unique ID of this invitation

        :returns: True if invitation was expired, False if not found
        :rtype: bool
        """
        invitation = self.session.query(Invitation).filter_by(id=invitation_id).first()
        if not invitation:
            return False
        invitation.expires_on = datetime.now()
        self.session.flush()
        return True
