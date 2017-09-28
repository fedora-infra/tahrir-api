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


def award(dburi=MOCK_URI, badge_id='fossbox', person_email='person@email.com'):
    db = TahrirDatabase(dburi)
    issued_on = None
    db.add_person(person_email)
    db.add_assertion(badge_id, person_email, issued_on)
