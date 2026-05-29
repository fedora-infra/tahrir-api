from sqlalchemy import and_, func

from ..model import Milestone
from ..utils import autocommit


class MilestoneMethod:
    """Milestone CRUD operations."""

    def milestone_exists(self, milestone_id):
        """
        Check to see if this milestone already exists in the database

        :type milestone_id: str
        :param milestone_id: The ID of a Milestone
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id).count() != 0

    def milestone_exists_for_badge_series(self, badge_id, series_id):
        """
        Check if the milestone with the given series and badge id exists

        :type badge_id: str
        :param badge_id: The ID of the badge

        :type series_id: str
        :param series_id: The ID of the series
        """
        return self.get_milestone_from_badge_series(badge_id, series_id).count() != 0

    def get_milestone_from_badge_series(self, badge_id, series_id):
        """
        Return the milestone with the given series and badge id

        :type badge_id: str
        :param badge_id: The ID of the badge

        :type series_id: str
        :param series_id: The ID of the series
        """
        return self.session.query(Milestone).filter(
            and_(
                Milestone.series_id == func.lower(series_id),
                Milestone.badge_id == func.lower(badge_id),
            )
        )

    def get_milestone(self, milestone_id):
        """
        Return the matching milestone from the database

        :type milestone_id: str
        :param milestone_id: The ID of a Milestone
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id)

    def get_all_milestones(self, series_id):
        """
        Returns all the milestones for the series

        :type series_id: str
        :param series_id: The id of the Series
        """
        return self.session.query(Milestone).filter(Milestone.series_id == series_id).all()

    @autocommit
    def create_milestone(self, position, badge_id, series_id):
        """
        Adds a new milestone to the database

        :type name: int
        :param name: position of the milestone in the series

        :type badge_id: str
        :param badge_id: Badge ID for the Milestone

        :type series_id: str
        :param series_id: ID of the Series
        """
        milestone = self.get_milestone_from_badge_series(badge_id, series_id).first()
        if not milestone:
            milestone = Milestone(position=position, badge_id=badge_id, series_id=series_id)

            self.session.add(milestone)
            self.session.flush()
        milestone_id = milestone.id

        return milestone_id

    def get_milestone_from_series_ids(self, series_ids):
        """
        Return list of milestones for the list of series ids

        :type series: list
        :param series: list of series ids
        """
        milestones = self.session.query(Milestone).filter(Milestone.series_id.in_(series_ids)).all()

        seen = set()
        unique_milestones = []

        for milestone in milestones:
            milestone_meta = (milestone.series_id, milestone.id)
            if milestone_meta not in seen:
                seen.add(milestone_meta)
                unique_milestones.append(milestone)

        return unique_milestones
