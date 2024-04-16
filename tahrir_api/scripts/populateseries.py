import os
import re
import sys

from ..model import Badge, Milestone, Series
from .utils import get_db_manager_from_paste


def usage(argv):
    cmd = os.path.basename(argv[0])
    print(f"usage: {cmd} <config_uri>\n '(example: \"{cmd} development.ini\"'")
    sys.exit(1)


_ROMAN_TO_ARABIC = dict(
    [("I", 1), ("V", 5), ("X", 10), ("L", 50), ("C", 100), ("D", 500), ("M", 1000)]
)
_REPLACEMENTS = [
    ("CM", "DCCCC"),
    ("CD", "CCCC"),
    ("XC", "LXXXX"),
    ("XL", "XXXX"),
    ("IX", "VIIII"),
    ("IV", "IIII"),
]
# A name of a badge in series must end with parenthesised series name and
# ordinal number, either in arabic or roman numerals. All badges in a given
# series must share the same series name.
_SERIES_NAME_RE = re.compile(r".+ \((?P<name>.+) (?P<ord>[0-9IXVL]+)\)")


def _convert(mapping, x):
    for prefix, replacement in mapping:
        x = x.replace(prefix, replacement)
    return x


def _to_number(x):
    """Convert a string with Roman numerals into an integer."""
    total = 0
    for c in _convert(_REPLACEMENTS, x):
        total += _ROMAN_TO_ARABIC[c]
    return total


def get_series_name(name):
    """Given a badge name, return a tuple of series name and ordinal number of
    this badge in the series.

    If the badge is not in any series, both tuple elements are None.
    """
    m = _SERIES_NAME_RE.match(name)
    if not m:
        return None, None
    base = m.group("name")
    idx = m.group("ord")
    try:
        try:
            return base, int(idx)
        except ValueError:
            return base, _to_number(idx)
    except (ValueError, KeyError):
        return None, None


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    db_mgr = get_db_manager_from_paste(config_uri)
    with db_mgr.Session() as session:
        for badge in session.query(Badge).all():
            if badge.milestone:
                # Skip badges that already are in some series.
                continue
            series_name, ordering = get_series_name(badge.name)
            if series_name and ordering:
                series = session.query(Series).filter(Series.name == series_name).first()

                if not series:
                    print(
                        f"Series <{series_name}> does not exist, skipping "
                        f"processing badge {badge.name}"
                    )
                    continue
                milestone = Milestone()
                milestone.badge_id = badge.id
                milestone.position = ordering
                milestone.series_id = series_name.lower().replace(" ", "-")
                session.add(milestone)
        session.commit()
