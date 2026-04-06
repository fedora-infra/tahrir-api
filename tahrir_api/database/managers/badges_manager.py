# Authors: Ross Delinger
#          Remy D <remyd@civx.us>
# Description: Badge management module for Tahrir database

from sqlalchemy import and_, func

from ...model import Badge
from ...utils import autocommit, convert_name_to_id
from .base import BaseManager


class BadgeManager(BaseManager):
    """Handles badge-related database operations"""

    def badge_exists(self, badge_id):
        """
        Check to see if this badge already exists in the database

        :type badge_id: str
        :param badge_id: The ID of a Badge
        """

        return (
            self.session.query(Badge).filter(func.lower(Badge.id) == func.lower(badge_id)).count()
            != 0
        )

    def get_badge(self, badge_id):
        """
        Return the badge with the given ID

        :type badge_id: str
        :param badge_id: The ID of the badge to return
        """

        if self.badge_exists(badge_id):
            return (
                self.session.query(Badge).filter(func.lower(Badge.id) == func.lower(badge_id)).one()
            )
        return None

    def get_badges(self, badge_ids):
        """
        Return the badges with the given IDs

        :type badge_ids: list
        :param badge_ids: The list of badge IDs
        """
        badges = self.session.query(Badge).filter(Badge.id.in_(badge_ids)).all()

        return badges

    def get_badges_from_tags(self, tags, match_all=False):
        """
        Return badges matching tags.

        :type tags: list
        :param tags: A list of string badge tags

        :type match_all: boolean
        :param match_all: Returned badges must have all tags in list
        """

        badges = list()

        if match_all:
            # Return badges matching all tags
            # ... by doing argument-expansion on a list comprehension
            badges.extend(
                self.session.query(Badge).filter(
                    and_(*[func.lower(Badge.tags).contains(str(tag + ",").lower()) for tag in tags])
                )
            )
        else:
            # Return badges matching any of the tags
            for tag in tags:
                badges.extend(
                    self.session.query(Badge)
                    .filter(func.lower(Badge.tags).contains(str(tag + ",").lower()))
                    .all()
                )

        # Eliminate any duplicates.
        unique_badges = list()
        for badge in badges:
            if badge not in unique_badges:
                unique_badges.append(badge)

        return unique_badges

    def get_badges_from_team(self, team_id):
        """
        Returns all the badges related to a team

        :type team_id: str
        :param team_id: id of the team
        """
        if self.teams.team_exists(team_id):
            series = self.series.get_series_from_team(team_id)
            series_ids = [elem.id for elem in series]

            milestones = self.milestones.get_milestone_from_series_ids(series_ids)
            badge_ids = list(set([milestone.badge_id for milestone in milestones]))

            badges = self.get_badges(badge_ids)
            return badges
        return None

    def get_all_badges(self):
        """
        Get all badges in the db.
        """

        return self.session.query(Badge)

    @autocommit
    def delete_badge(self, badge_id):
        """
        Delete a badge from the database

        :type badge_id: str
        :param badge_id: ID of the badge to delete
        """

        if self.badge_exists(badge_id):
            to_delete = self.session.query(Badge).filter_by(id=badge_id).one()
            self.session.delete(to_delete)
            self.session.flush()
            return badge_id
        return False

    @autocommit
    def add_badge(self, name, image, desc, criteria, issuer_id, tags=None, badge_id=None):
        """
        Add a new badge to the database

        :type name: str
        :param name: Name of the Badge

        :type image: str
        :param image: URL of the image for this Badge

        :type criteria: str
        :param criteria: The criteria of this Badge

        :type issuer_id: int
        :param issuer_id: The ID of the issuer who issues this Badge

        :type tags: str
        :param tags: Comma-delimited list of badge tags.
        """

        if not badge_id:
            badge_id = convert_name_to_id(name)

        if not self.badge_exists(badge_id):
            # Make sure the tags string has a trailing
            # comma at the end. The tags view in Tahrir
            # depends on that comma when matching all
            # tags.
            if tags and not tags.endswith(","):
                tags = tags + ","

            # Actually add the badge.
            new_badge = Badge(
                id=badge_id,
                name=name,
                image=image,
                description=desc,
                criteria=criteria,
                issuer_id=issuer_id,
                tags=tags,
            )
            self.session.add(new_badge)
            self.session.flush()
        return badge_id

    @autocommit
    def update_badge(self, badge_id: str, **kwargs):
        """
        Update a badge in the database

        :type badge_id: str
        :param badge_id: Badge ID
        :param kwargs: Fields to update. Allowed fields are:
            - name: Badge name
            - image: Badge image URL
            - description: Badge description
            - criteria: Badge criteria
            - tags: Badge tags (comma will be auto-appended if missing)

        :raises KeyError: If invalid field names are provided
        :returns: badge_id if successful, False if badge doesn't exist
        """

        badge = self.get_badge(badge_id)
        if not badge:
            return False

        # List of allowed fields to update
        allowed_fields = ["name", "image", "description", "criteria", "tags"]

        # Check for invalid fields
        invalid_fields = set(kwargs.keys()) - set(allowed_fields)
        if invalid_fields:
            raise KeyError(f"Invalid fields: {invalid_fields}")

        for attr, value in kwargs.items():
            # Special handling for tags
            if attr == "tags":
                value = value + "," if value and not value.endswith(",") else value
            setattr(badge, attr, value)

        self.session.flush()
        return badge_id
