from datetime import datetime, timezone

from sqlalchemy import func
from tahrir_messages import BadgeAwardV1

from ..model import Assertion
from ..utils import autocommit


class AssertionMethod:
    """Assertion (badge award) CRUD operations."""

    def get_all_assertions(self, begin: int | None = None, limit: int | None = None):
        """
        Get all assertions in the db, ordered by most recent first.

        :type begin: int
        :param begin: Number of assertions to skip (offset for pagination, default: 0)

        :type limit: int
        :param limit: Maximum number of assertions to return (default: 100)
        """

        result = self.session.query(Assertion).order_by(Assertion.issued_on.desc())

        if begin is not None or limit is not None:
            result = result.offset(begin or 0).limit(limit)

        return result

    def get_assertions_by_email(self, person_email):
        """
        Get all assertions attached to the given email

        :type person_email: str
        :param person_email: Email of the person to get assertions for
        """

        person = self.get_person(person_email=person_email)
        if person is None:
            return False
        return self.session.query(Assertion).filter_by(person_id=person.id).all()

    def get_assertions_by_badge(self, badge_id: str, begin: int = 0, limit: int = 100):
        """
        Get all assertions of a particular badge.

        :type begin: int
        :param begin: Number of assertions to skip (offset for pagination)

        :type limit: int
        :param limit: Maximum number of assertions to return

        :type badge_id: str
        :param badge_id: Badge id to get assertions for.
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Assertion)
                .filter(func.lower(Assertion.badge_id) == func.lower(badge_id))
                .order_by(Assertion.issued_on.desc())
                .offset(begin)
                .limit(limit)
                .all()
            )
        else:
            return False

    def get_assertions_count_by_badge(self, badge_id: str):
        """
        Get the assertions count for a particular badge using SQL COUNT.

        :type badge_id: str
        :param badge_id: Badge id to count assertions for.
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(func.count(Assertion.id))
                .filter(func.lower(Assertion.badge_id) == func.lower(badge_id))
                .scalar()
            )
        return 0

    def get_origin_assertion_by_badge(self, badge_id: str):
        """
        Get the origin assertion for a particular badge.

        :type badge_id: str
        :param badge_id: Badge id to get the first assertion for.
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Assertion)
                .filter(func.lower(Assertion.badge_id) == func.lower(badge_id))
                .order_by(Assertion.issued_on.asc())
                .first()
            )
        return False

    def get_recent_assertion_by_badge(self, badge_id: str):
        """
        Get the recent assertion for a particular badge.

        :type badge_id: str
        :param badge_id: Badge id to get the last assertion for.
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Assertion)
                .filter(func.lower(Assertion.badge_id) == func.lower(badge_id))
                .order_by(Assertion.issued_on.desc())
                .first()
            )
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

        badge = self.get_badge(badge_id)
        person = self.get_person(person_email)

        if not badge or not person:
            return False

        if badge.legacy:
            raise ValueError(f"Badge {badge_id!r} is a legacy badge and cannot be awarded")

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

        return person_email, badge_id

    @autocommit
    def remove_assertion(self, badge_id, person_email):
        """
        Remove an assertion (revoke a badge) from the database

        :type badge_id: str
        :param badge_id: ID of the badge to be revoked

        :type person_email: str
        :param person_email: Email of the Person to revoke the badge from

        :returns: True if successful, False otherwise
        """

        person = self.get_person(person_email)
        if not person:
            return False

        assertion = (
            self.session.query(Assertion).filter_by(person_id=person.id, badge_id=badge_id).first()
        )

        if not assertion:
            return False

        self.session.delete(assertion)
        self.session.flush()

        return True
