from ..model import Issuer
from ..utils import autocommit


class IssuerMethod:
    """Issuer CRUD operations."""

    def issuer_exists(self, origin, name):
        """
        Check to see if an issuer with this ID is in the database

        :type issuer_id: int
        :param issuer_id: The unique ID of this issuer
        """

        return self.session.query(Issuer).filter_by(origin=origin, name=name).count() != 0

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
