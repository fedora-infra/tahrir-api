from sqlalchemy import func

from ..model import Series
from ..utils import autocommit, convert_name_to_id


class SeriesMethod:
    """Series CRUD operations."""

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
        if self.team_exists(team_id):
            return self.session.query(Series).filter(Series.team_id == team_id).all()

    @autocommit
    def create_series(self, name, desc, team_id, tags=None, series_id=None):
        """
        Adds a new series to the database

        :type name: str
        :param name: Name of the Series

        :type desc: str
        :param desc: Description of the Series

        :type team_id: str
        :param team_id: Team Id to which this Series belongs to

        :type tags: str | list[str]
        :param tags: Tags for a Series (comma-separated string or list of names)

        :type series_id: str
        :param series_id: ID of the Series
        """

        if not series_id:
            series_id = convert_name_to_id(name)

        if not self.series_exists(series_id):
            new_series = Series(id=series_id, name=name, description=desc, team_id=team_id)

            if tags:
                self._set_series_tags(new_series, tags)

            self.session.add(new_series)
            self.session.flush()
        return series_id

    def get_all_series(self):
        """
        Get all series in the db.
        """

        return self.session.query(Series)
