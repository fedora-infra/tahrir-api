# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: Series management module for Tahrir database

from sqlalchemy import func

from ...model import Series
from ...utils import autocommit, convert_name_to_id
from .base import BaseManager


class SeriesManager(BaseManager):
    """Handles series-related database operations"""

    def series_exists(self, series_id):
        """
        Check to see if this series already exists in the database

        :type series_id: str
        :param series_id: The ID of a Series
        """
        return (
            self.session.query(Series)
            .filter(func.lower(Series.id) == func.lower(series_id))
            .count()
            != 0
        )

    def get_series(self, series_id):
        """
        Return the series with the given ID

        :type series_id: str
        :param series_id: The ID of the series to return
        """
        if self.series_exists(series_id):
            return (
                self.session.query(Series)
                .filter(func.lower(Series.id) == func.lower(series_id))
                .one()
            )
        return None

    def get_series_from_team(self, team_id):
        """
        Return the series related to a given team ID

        :type team_id: str
        :param team_id: The ID of the team
        """
        if self.teams and self.teams.team_exists(team_id):
            return self.session.query(Series).filter(Series.team_id == team_id).all()
        return None

    @autocommit
    def create_series(self, name, desc, team_id, tags=None, series_id=None):
        """
        Adds a new series to the database

        :type name: str
        :param name: The name of the series
        :type desc: str
        :param desc: The description of the series
        :type team_id: str
        :param team_id: The ID of the team
        :type tags: str
        :param tags: The tags for the series
        :type series_id: str
        :param series_id: The ID of the series
        """
        if not series_id:
            series_id = convert_name_to_id(name)

        if not self.series_exists(series_id):
            new_series = Series(
                id=series_id, name=name, description=desc, team_id=team_id, tags=tags
            )
            self.session.add(new_series)
            self.session.flush()
        return series_id

    def get_all_series(self):
        """
        Get all series in the database
        """
        return self.session.query(Series)
