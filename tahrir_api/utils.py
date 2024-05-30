""" Module to keep random utils. """

import importlib.resources

from sqlalchemy_helpers import DatabaseManager


def autocommit(func):
    """A decorator that autocommits after API calls unless
    configured otherwise.
    """

    def _wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.autocommit:
            self.session.commit()
        return result

    _wrapper.__name__ = func.__name__
    _wrapper.__doc__ = func.__doc__

    return _wrapper


def convert_name_to_id(name):
    """
    Convert a badge name into a valid badge ID.

    :type name: string
    :param name: The badge name to convert to an ID
    """

    badge_id = name.lower().replace(" ", "-")
    bad = ['"', "'", "(", ")", "*", "&", "?"]
    replacements = dict(zip(bad, [""] * len(bad)))
    for a, b in replacements.items():
        badge_id = badge_id.replace(a, b)

    return badge_id


def get_db_manager_from_uri(uri):
    from .model import DeclarativeBase  # noqa: F401

    with importlib.resources.as_file(
        importlib.resources.files("tahrir_api").joinpath("migrations")
    ) as alembic_path:
        return DatabaseManager(uri, alembic_path.as_posix())
