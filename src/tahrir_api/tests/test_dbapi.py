#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import unittest

from sqlalchemy import create_engine

from tahrir_api.dbapi import TahrirDatabase

from tahrir_api.model import DBSession
from tahrir_api.model import DeclarativeBase

from subprocess import check_output as _check_output

metadata = getattr(DeclarativeBase, 'metadata')


def check_output(cmd):
    try:
        return _check_output(cmd)
    except Exception:
        return None


class TestDBInit(unittest.TestCase):

    def setUp(self):
        check_output(['touch', 'testdb.db'])
        sqlalchemy_uri = "sqlite:///testdb.db"
        engine = create_engine(sqlalchemy_uri)
        DBSession.configure(bind=engine)
        metadata.create_all(engine)

        self.callback_calls = []
        self.api = TahrirDatabase(
            sqlalchemy_uri,
            notification_callback=self.callback)

    def tearDown(self):
        check_output(['rm', 'testdb.db'])
        self.callback_calls = []

    def callback(self, *args, **kwargs):
        self.callback_calls.append((args, kwargs))

    def test_add_badges(self):
        self.api.add_badge(
            u"TestBadge",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            1337
        )

        assert self.api.badge_exists("testbadge") is True

    def test_add_team(self):
        self.api.create_team("TestTeam")

        assert self.api.team_exists("testteam") is True

    def test_add_series(self):
        team_id = self.api.create_team(u"TestTeam")

        self.api.create_series(u"TestSeries",
                               u"A test series",
                               team_id,
                               u"test, series")

        assert self.api.series_exists("testseries") is True

    def test_add_milestone(self):
        team_id = self.api.create_team(u"TestTeam")

        series_id = self.api.create_series(u"TestSeries",
                                           u"A test series",
                                           team_id,
                                           u"test, series")

        badge_id_1 = self.api.add_badge(
            u"TestBadge-1",
            u"TestImage-2",
            u"A test badge for doing 10 unit tests",
            u"TestCriteria",
            1337
        )

        badge_id_2 = self.api.add_badge(
            u"TestBadge-2",
            u"TestImage-2",
            u"A test badge for doing 100 unit tests",
            u"TestCriteria",
            1337
        )

        milestone_id_1 = self.api.create_milestone(1,
                                                   badge_id_1,
                                                   series_id)

        milestone_id_2 = self.api.create_milestone(2,
                                                   badge_id_2,
                                                   series_id)

        assert self.api.milestone_exists(milestone_id_1) is True
        assert self.api.milestone_exists(milestone_id_2) is True

    def test_add_person(self):
        self.api.add_person(u"test@tester.com")
        assert self.api.person_exists(u"test@tester.com") is True

    def test_add_issuer(self):
        _id = self.api.add_issuer(
            u"TestOrigin",
            u"TestName",
            u"TestOrg",
            u"TestContact"
        )
        assert self.api.issuer_exists("TestOrigin", "TestName") is True

    def test_add_invitation(self):
        badge_id = self.api.add_badge(
            u"TestBadge",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            1337
        )
        _id = self.api.add_invitation(
            badge_id,
        )

        assert self.api.invitation_exists(_id)

    def test_last_login(self):
        email = u"test@tester.com"
        person_id = self.api.add_person(email)
        person = self.api.get_person(person_id)
        assert not person.last_login
        self.api.note_login(nickname=person.nickname)
        assert person.last_login

    def test_add_assertion(self):
        issuer_id = self.api.add_issuer(
            u"TestOrigin",
            u"TestName",
            u"TestOrg",
            u"TestContact"
        )
        badge_id = self.api.add_badge(
            u"TestBadge",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
        )
        email = u"test@tester.com"
        self.api.add_person(email)
        self.api.add_assertion(badge_id, email, None, 'link')
        assert self.api.assertion_exists(badge_id, email)

        badge = self.api.get_badge(badge_id)
        assert badge.assertions[0].issued_for == 'link'

        # Ensure that we would have published two fedmsg messages for that.
        assert len(self.callback_calls) == 2

        # Ensure that the first message had a 'badge_id' in the message.
        assert 'badge_id' in self.callback_calls[0][1]['msg']['badge']

    def test_get_badges_from_tags(self):
        issuer_id = self.api.add_issuer(
            u"TestOrigin",
            u"TestName",
            u"TestOrg",
            u"TestContact"
        )

        # Badge tagged with "test"
        self.api.add_badge(
            u"TestBadgeA",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
            tags=u"test"
        )

        # Badge tagged with "tester"
        self.api.add_badge(
            u"TestBadgeB",
            u"TestImage",
            u"A second test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
            tags=u"tester"
        )

        # Badge tagged with both "test" and "tester"
        self.api.add_badge(
            u"TestBadgeC",
            u"TestImage",
            u"A third test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
            tags=u"test, tester"
        )

        tags = ['test', 'tester']
        badges_any = self.api.get_badges_from_tags(tags, match_all=False)
        assert len(badges_any) == 3
        badges_all = self.api.get_badges_from_tags(tags, match_all=True)
        assert len(badges_all) == 1
