from ..model import Authorization
from ..utils import autocommit


class AuthorizationMethod:
    """Authorization (badge admin rights) operations."""

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
            badge = self.get_badge(badge_id)

            if badge.legacy:
                raise ValueError(f"Badge {badge_id!r} is a legacy badge and cannot be authorized")

            person = self.get_person(person_email)

            new_authz = Authorization(badge_id=badge_id, person_id=person.id)
            self.session.add(new_authz)
            self.session.flush()

            return (person_email, badge_id)

        return False

    @autocommit
    def delete_authorization(self, badge_id, person_email):
        """
        Delete an authorization (remove someone's admin rights for a certain badge)

        :type badge_id: str
        :param badge_id: ID of the badge

        :type person_email: str
        :param person_email: Email of the Person to remove rights from
        """

        person = self.get_person(person_email)
        if not person:
            return False

        authorization = (
            self.session.query(Authorization)
            .filter_by(person_id=person.id, badge_id=badge_id)
            .first()
        )

        if authorization:
            self.session.delete(authorization)
            self.session.flush()
            return (person_email, badge_id)

        return False
