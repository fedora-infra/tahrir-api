from sqlalchemy import and_, func, or_

from ..model import Badge, Tag
from ..utils import autocommit, convert_name_to_id


class BadgeMethod:
    """Badge CRUD, search, and rarity operations."""

    def get_badges_from_team(self, team_id, include_legacy=False):
        """
        Returns all the badges related to a team

        :type team_id: str
        :param team_id: id of the team

        :type include_legacy: boolean
        :param include_legacy: Include legacy badges in results (default: False)
        """
        if self.team_exists(team_id):
            series = self.get_series_from_team(team_id)
            series_ids = [elem.id for elem in series]

            milestones = self.get_milestone_from_series_ids(series_ids)
            badge_ids = list(set([milestone.badge_id for milestone in milestones]))

            return self.get_badges(badge_ids, include_legacy=include_legacy)
        return None

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

    def get_badges(self, badge_ids, include_legacy=False):
        """
        Return the badges with the given IDs

        :type badge_ids: list
        :param badge_ids: The list of badge IDs

        :type include_legacy: boolean
        :param include_legacy: Include legacy badges in results (default: False)
        """
        query = self.session.query(Badge).filter(Badge.id.in_(badge_ids))
        if not include_legacy:
            query = query.filter(Badge.legacy.is_(False))
        return query.all()

    def get_badges_from_tags(self, tags, match_all=False, include_legacy=False):
        """
        Return badges matching tags.

        :type tags: list[str]
        :param tags: A list of badge tag names

        :type match_all: boolean
        :param match_all: Returned badges must have all tags in list

        :type include_legacy: boolean
        :param include_legacy: Include legacy badges in results (default: False)
        """

        badges = []

        if match_all:
            # Return badges matching all tags
            # ... by doing argument-expansion on a list comprehension
            query = self.session.query(Badge).filter(
                and_(*[Badge.tags.any(func.lower(Tag.name) == func.lower(tag)) for tag in tags])
            )
            if not include_legacy:
                query = query.filter(Badge.legacy.is_(False))
            badges.extend(query)
        else:
            # Return badges matching any of the tags (deduplicated via distinct)
            query = (
                self.session.query(Badge)
                .filter(
                    or_(*[Badge.tags.any(func.lower(Tag.name) == func.lower(tag)) for tag in tags])
                )
                .distinct()
            )
            if not include_legacy:
                query = query.filter(Badge.legacy.is_(False))
            badges.extend(query.all())

        return badges

    def get_all_badges(self, include_legacy=False):
        """
        Get all badges in the db.

        :type include_legacy: boolean
        :param include_legacy: Include legacy badges in results (default: False)
        """

        query = self.session.query(Badge)
        if not include_legacy:
            query = query.filter(Badge.legacy.is_(False))
        return query

    @autocommit
    def delete_badge(self, badge_id):
        """
        Delete a badge from the database

        :type badge_id: str
        :param badge_id: ID of the badge to delete

        :raises ValueError: If the badge is marked as legacy
        """

        if self.badge_exists(badge_id):
            to_delete = self.session.query(Badge).filter_by(id=badge_id).one()
            if to_delete.legacy:
                raise ValueError(f"Badge {badge_id!r} is a legacy badge and cannot be deleted")
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

        :type tags: list[str]
        :param tags: List of tag names for this Badge.
        """

        if not badge_id:
            badge_id = convert_name_to_id(name)

        if not self.badge_exists(badge_id):
            # Actually add the badge.
            new_badge = Badge(
                id=badge_id,
                name=name,
                image=image,
                description=desc,
                criteria=criteria,
                issuer_id=issuer_id,
            )

            if tags:
                self._set_badge_tags(new_badge, tags)

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
            - tags: Badge tags (list of tag name strings)
            - legacy: Badge legacy status (boolean)

        :raises KeyError: If invalid field names are provided
        :returns: badge_id if successful, False if badge doesn't exist
        """

        badge = self.get_badge(badge_id)
        if not badge:
            return False

        # List of allowed fields to update
        allowed_fields = ["name", "image", "description", "criteria", "tags", "legacy"]

        # Check for invalid fields
        invalid_fields = set(kwargs.keys()) - set(allowed_fields)
        if invalid_fields:
            raise KeyError(f"Invalid fields: {invalid_fields}")

        for attr, value in kwargs.items():
            # Special handling for tags
            if attr == "tags":
                self._set_badge_tags(badge, value)
            else:
                setattr(badge, attr, value)

        self.session.flush()
        return badge_id

    def get_badges_by_string(self, search_string, begin=0, limit=100, include_legacy=False):
        """
        Get badges matching a search string in their name, description or tags with pagination.

        :type search_string: str
        :param search_string: The string to search for badges.
        :type begin: int
        :param begin: Offset for pagination (default 0).
        :type limit: int
        :param limit: Max results per page, capped at 100 (default 100).

        :type include_legacy: boolean
        :param include_legacy: Include legacy badges in results (default: False)
        """
        safe_limit = min(limit, 100)

        query = self.session.query(Badge).filter(
            func.lower(Badge.name).like(f"%{search_string.lower()}%")
            | func.lower(Badge.description).like(f"%{search_string.lower()}%")
            | Badge.tags.any(func.lower(Tag.name).like(f"%{search_string.lower()}%"))
        )

        # Filter out legacy badges
        if not include_legacy:
            query = query.filter(Badge.legacy.is_(False))

        total_count = query.count()
        paginated_results = query.offset(begin).limit(safe_limit).all()
        return {
            "badges": paginated_results,
            "total": total_count,
            "begin": begin,
            "limit": safe_limit,
        }
