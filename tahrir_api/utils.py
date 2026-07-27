"""Module to keep random utils."""

import importlib.resources
from collections.abc import Callable
from functools import wraps
from typing import Any

from sqlalchemy_helpers import DatabaseManager


def autocommit(func: Callable[..., Any]) -> Callable[..., Any]:
    """A decorator that autocommits after API calls unless
    configured otherwise.
    """

    @wraps(func)
    def _wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = func(self, *args, **kwargs)
        if self.autocommit:
            self.session.commit()
        return result

    return _wrapper


def convert_name_to_id(name: str) -> str:
    """
    Convert a badge name into a valid badge ID.

    :type name: string
    :param name: The badge name to convert to an ID
    """

    badge_id = name.lower().replace(" ", "-")
    bad = ['"', "'", "(", ")", "*", "&", "?"]
    replacements = dict(zip(bad, [""] * len(bad), strict=False))
    for a, b in replacements.items():
        badge_id = badge_id.replace(a, b)

    return badge_id


def get_db_manager_from_uri(uri: str) -> DatabaseManager:
    from .model import DeclarativeBase  # noqa: F401

    with importlib.resources.as_file(
        importlib.resources.files("tahrir_api").joinpath("migrations")
    ) as alembic_path:
        return DatabaseManager(uri, alembic_path.as_posix())
