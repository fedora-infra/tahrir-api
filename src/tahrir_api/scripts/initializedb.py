#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys

from sqlalchemy import engine_from_config

from paste.deploy import appconfig

from tahrir_api.model import DBSession
from tahrir_api.model import DeclarativeBase

metadata = getattr(DeclarativeBase, 'metadata')

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

    settings = appconfig(config_name, name=section, 
                         relative_to=here_dir,
                         global_conf=global_conf)

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    metadata.create_all(engine)

#   Skip all the following... just leaving it for posterity
#   with transaction.manager:
#         issuer = Issuer(
#             name="Ralph Bean",
#             origin="http://badges.threebean.org",
#             org="threebean.org",
#             contact="rbean@redhat.com",
#         )
#         DBSession.add(issuer)
#         badge = Badge(
#             name="Plus One!",
#             image="/pngs/threebean-plus-one.png",
#             description="""
#             Got a recommendation from threebean for being awesome.
#             """.strip(),
#             criteria="/badges/plus-one",  # TODO -- how should this work?
#             issuer=issuer,
#         )
#         DBSession.add(badge)
#         person = Person(
#             email="rbean@redhat.com",
#         )
#         DBSession.add(person)
#         assertion = Assertion(
#             badge=badge,
#             person=person,
#             issued_on=datetime.datetime.now(),
#         )
#
#         DBSession.add(assertion)
#         pprint.pprint(assertion.__json__())
