#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from tahrir_api.dbapi import TahrirDatabase

MOCK_URI = 'backend://badges:badgesareawesome@localhost/badges'


def database(dburi=MOCK_URI):
    return TahrirDatabase(dburi)


def add_issuer(db):
    origin = 'http://foss.rit.edu/badges'
    issuer_name = 'FOSS@RIT'
    org = 'http://foss.rit.edu'
    contact = 'foss@rit.edu'
    issuer_id = db.add_issuer(origin, issuer_name, org, contact)
    return issuer_id


def add_badge(db, issuer_id):
    badge_name = 'fossbox'
    image = 'http://foss.rit.edu/files/fossboxbadge.png'
    desc = 'Welcome to the FOSSBox. A member is you!'
    criteria = 'http://foss.rit.edu'
    db.add_badge(badge_name, image, desc, criteria, issuer_id)
