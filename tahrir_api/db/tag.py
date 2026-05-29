from ..model import Tag
from ..utils import autocommit


class TagMethod:
    """Tag CRUD and normalisation helpers."""

    def get_tag(self, tag_name):
        """Return the tag with the given name, or None if it does not exist."""
        return self.session.query(Tag).filter_by(name=tag_name).first()

    @autocommit
    def create_tag(self, tag_name):
        """Create and return a new tag with the given name."""
        tag = Tag(name=tag_name)
        self.session.add(tag)
        self.session.flush()
        return tag

    @autocommit
    def cleanup_orphan_tags(self):
        """
        Delete tags that are not associated with any badge or series.

        Intended to be run regularly (e.g. once per day) to keep the tags
        table free of stale entries.

        :returns: The number of orphan tags deleted.
        """
        orphans = self.session.query(Tag).filter(~Tag.badges.any()).filter(~Tag.series.any()).all()
        for tag in orphans:
            self.session.delete(tag)
        self.session.flush()
        return len(orphans)

    def _normalize_tags(self, tags):
        if isinstance(tags, str):
            tags = tags.split(",")
        seen = []
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if tag_name and tag_name not in seen:
                seen.append(tag_name)
        return [self.get_tag(name) or self.create_tag(name) for name in seen]

    def _set_badge_tags(self, badge, tags):
        badge.tags = self._normalize_tags(tags)

    def _set_series_tags(self, series, tags):
        series.tags = self._normalize_tags(tags)
