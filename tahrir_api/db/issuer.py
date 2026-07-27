from sqlalchemy.orm import Query

from ..model import Issuer
from ..utils import autocommit


class IssuerMethod:
    """Issuer CRUD operations."""

    def issuer_exists(self, origin: str, name: str) -> bool:
        """
        Check to see if an issuer with this ID is in the database

        :type issuer_id: int
        :param issuer_id: The unique ID of this issuer
        """

        return self.session.query(Issuer).filter_by(origin=origin, name=name).count() != 0

    def get_issuer(self, issuer_id: int) -> Issuer | None:
        """
        Return the issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to return
        """
        return self.session.query(Issuer).filter_by(id=issuer_id).first()

    @autocommit
    def delete_issuer(self, issuer_id: int) -> int | bool:
        """
        Delete an issuer with the given ID

        :type issuer_id: int
        :param issuer_id: ID of the issuer to be delete
        """

        issuer = self.session.query(Issuer).filter_by(id=issuer_id).first()
        if not issuer:
            return False
        self.session.delete(issuer)
        self.session.flush()
        return issuer_id

    @autocommit
    def add_issuer(self, origin: str, name: str, org: str, contact: str) -> int:
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

        issuer = self.session.query(Issuer).filter_by(origin=origin, name=name).first()
        if issuer:
            return issuer.id

        new_issuer = Issuer(origin=origin, name=name, org=org, contact=contact)
        self.session.add(new_issuer)
        self.session.flush()
        return new_issuer.id

    def get_all_issuers(self) -> Query[Issuer]:
        """
        Get all issuers in the db.
        """

        return self.session.query(Issuer)
