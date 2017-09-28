#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import re
import sys
import transaction

from sqlalchemy import engine_from_config

from paste.deploy import appconfig

from tahrir_api.model import Badge
from tahrir_api.model import Series
from tahrir_api.model import DBSession
from tahrir_api.model import Milestone

_ROMAN_TO_ARABIC = dict([
    ('I', 1),
    ('V', 5),
    ('X', 10),
    ('L', 50),
    ('C', 100),
    ('D', 500),
    ('M', 1000),
])
_REPLACEMENTS = [
    ('CM', 'DCCCC'),
    ('CD', 'CCCC'),
    ('XC', 'LXXXX'),
    ('XL', 'XXXX'),
    ('IX', 'VIIII'),
    ('IV', 'IIII'),
]

# A name of a badge in series must end with parenthesised series name and
# ordinal number, either in arabic or roman numerals. All badges in a given
# series must share the same series name.
_SERIES_NAME_RE = re.compile(r'.+ \((?P<name>.+) (?P<ord>[0-9IXVL]+)\)')


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def _getpathsec(config_uri, name):
    if '#' in config_uri:
        path, section = config_uri.split('#', 1)
    else:
        path, section = config_uri, 'main'
    if name:
        section = name
    return path, section


def _convert(mapping, x):
    for prefix, replacement in mapping:
        x = x.replace(prefix, replacement)
    return x


def _to_number(x):
    """
    Convert a string with Roman numerals into an integer.
    """
    total = 0
    for c in _convert(_REPLACEMENTS, x):
        total += _ROMAN_TO_ARABIC[c]
    return total


def get_series_name(name):
    """
    Given a badge name, return a tuple of series name and ordinal number of
    this badge in the series.

    If the badge is not in any series, both tuple elements are None.
    """
    m = _SERIES_NAME_RE.match(name)
    if not m:
        return None, None
    base = m.group('name')
    idx = m.group('ord')
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
    path, section = _getpathsec(config_uri, "pyramid")
    config_name = 'config:%s' % path
    here_dir = os.getcwd()

    global_conf = None
    if 'OPENSHIFT_APP_NAME' in os.environ:
        if 'OPENSHIFT_MYSQL_DB_URL' in os.environ:
            template = '{OPENSHIFT_MYSQL_DB_URL}{OPENSHIFT_APP_NAME}'
        elif 'OPENSHIFT_POSTGRESQL_DB_URL' in os.environ:
            template = '{OPENSHIFT_POSTGRESQL_DB_URL}{OPENSHIFT_APP_NAME}'

        global_conf = {
            'sqlalchemy.url': template.format(**os.environ)
        }

    settings = appconfig(config_name, name=section, relative_to=here_dir,
                         global_conf=global_conf)

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    db_session = DBSession  # pylint
    with transaction.manager:
        for badge in db_session.query(Badge).all():
            if badge.milestone:
                # Skip badges that already are in some series.
                continue
            series_name, ordering = get_series_name(badge.name)
            if series_name and ordering:
                series = db_session.query(Series) \
                                   .filter(Series.name == series_name).first()
                if not series:
                    print('Series <%s> does not exist, skipping '
                          'processing badge %s' % (series_name, badge.name))
                    continue
                milestone = Milestone()
                milestone.badge_id = badge.id
                milestone.position = ordering
                milestone.series_id = series_name.lower().replace(' ', '-')
                db_session.add(milestone)
