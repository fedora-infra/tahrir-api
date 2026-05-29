from sqlalchemy import func

from ..model import Team
from ..utils import autocommit, convert_name_to_id


class TeamMethod:
    """Team CRUD operations."""

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
