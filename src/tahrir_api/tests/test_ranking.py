#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_property

import unittest
import datetime

from subprocess import check_output as _check_output

from sqlalchemy import create_engine

from tahrir_api.dbapi import TahrirDatabase

from tahrir_api.model import Assertion
from tahrir_api.model import DBSession
from tahrir_api.model import DeclarativeBase

metadata = getattr(DeclarativeBase, 'metadata')

now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days=1)
one_week_ago = now - datetime.timedelta(days=7)
one_month_ago = now - datetime.timedelta(weeks=4)


def check_output(cmd):
    try:
        return _check_output(cmd)
    except Exception:
        return None


def assert_in(member, container):
    """ 
    Just like assertTrue(a in b), but with a nicer default message. 
    """
    assert_that(member,  is_in(container),
                '%r not found in %r' % (member, container))


class TestRanking(unittest.TestCase):

    def _create_test_data(self):
        issuer_id = self.api.add_issuer(
            u"TestOrigin",
            u"TestName",
            u"TestOrg",
            u"TestContact"
        )
        self.badge_id_1 = self.api.add_badge(
            u"TestBadge1",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
        )
        self.badge_id_2 = self.api.add_badge(
            u"TestBadge2",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
        )
        self.badge_id_3 = self.api.add_badge(
            u"TestBadge3",
            u"TestImage",
            u"A test badge for doing unit tests",
            u"TestCriteria",
            issuer_id,
        )
        self.email_1 = u"test_1@tester.com"
        self.api.add_person(self.email_1)
        self.email_2 = u"test_2@tester.com"
        self.api.add_person(self.email_2)
        self.email_3 = u"test_3@tester.com"
        self.api.add_person(self.email_3)
        self.email_4 = u"test_4@tester.com"
        self.api.add_person(self.email_4)

    def setUp(self):
        check_output(['touch', 'testdb.db'])
        sqlalchemy_uri = "sqlite:///testdb.db"
        engine = create_engine(sqlalchemy_uri)
        DBSession.configure(bind=engine)
        metadata.create_all(engine)

        self.api = TahrirDatabase(sqlalchemy_uri)
        self._create_test_data()

    def tearDown(self):
        check_output(['rm', 'testdb.db'])

    def test_ranking_simple(self):
        self.api.add_assertion(self.badge_id_1, self.email_1, None)

        self.api.add_assertion(self.badge_id_1, self.email_4, None)
        self.api.add_assertion(self.badge_id_2, self.email_4, None)
        self.api.add_assertion(self.badge_id_3, self.email_4, None)

        person1 = self.api.get_person("test_1@tester.com")
        person4 = self.api.get_person("test_4@tester.com")

        assert_that(person1, has_property('rank', is_(2)))
        assert_that(person4, has_property('rank', is_(1)))

    def test_ranking_tie(self):
        self.api.add_assertion(self.badge_id_1, self.email_1, None)

        self.api.add_assertion(self.badge_id_1, self.email_2, None)
        self.api.add_assertion(self.badge_id_2, self.email_2, None)

        self.api.add_assertion(self.badge_id_1, self.email_3, None)
        self.api.add_assertion(self.badge_id_2, self.email_3, None)

        self.api.add_assertion(self.badge_id_1, self.email_4, None)
        self.api.add_assertion(self.badge_id_2, self.email_4, None)
        self.api.add_assertion(self.badge_id_3, self.email_4, None)

        person1 = self.api.get_person("test_1@tester.com")
        person2 = self.api.get_person("test_2@tester.com")
        person3 = self.api.get_person("test_3@tester.com")
        person4 = self.api.get_person("test_4@tester.com")

        assert_that(person1, has_property('rank', is_(4)))
        assert_that(person2, has_property('rank', is_(2)))
        assert_that(person3, has_property('rank', is_(2)))
        assert_that(person4, has_property('rank', is_(1)))

    def test_ranking_preexisting(self):
        """ 
        Test that rank updating works for pre-existant users 
        """
        person1 = self.api.get_person("test_1@tester.com")
        new_assertion1 = Assertion(
            badge_id=self.badge_id_1,
            person_id=person1.id,
        )
        self.api.session.add(new_assertion1)
        new_assertion2 = Assertion(
            badge_id=self.badge_id_2,
            person_id=person1.id,
        )
        self.api.session.add(new_assertion2)
        self.api.session.flush()

        # For persons who existed *before* we added cached ranks, they should
        # have a null-rank.
        assert_that(person1, has_property('rank', is_(none())))

        # But once *anyone* else gets a badge, old ranks should be updated too.
        self.api.add_assertion(self.badge_id_1, self.email_2, None)
        assert_that(person1.rank, 1)

        person2 = self.api.get_person("test_2@tester.com")
        assert_that(person2, has_property('rank', is_(2)))

        # but people with no badges should still be null ranked.
        person3 = self.api.get_person("test_3@tester.com")
        assert_that(person3, has_property('rank', is_(none())))

    def test_ranking_with_time_limits(self):
        self.api.add_assertion(self.badge_id_1, self.email_1, yesterday)

        self.api.add_assertion(self.badge_id_1, self.email_4, yesterday)
        self.api.add_assertion(self.badge_id_2, self.email_4, one_week_ago)
        self.api.add_assertion(self.badge_id_3, self.email_4, one_month_ago)

        person1 = self.api.get_person("test_1@tester.com")
        person4 = self.api.get_person("test_4@tester.com")

        epsilon = datetime.timedelta(hours=1)

        results = self.api._make_leaderboard(yesterday - epsilon, now)
        assert_that(results,
                    has_entry(person1, has_entry('badges', is_(1))))
        assert_that(results,
                    has_entry(person4, has_entry('badges', is_(1))))

        results = self.api._make_leaderboard(one_week_ago - epsilon, now)
        assert_that(results,
                    has_entry(person1, has_entry('badges', is_(1))))
        assert_that(results,
                    has_entry(person4, has_entry('badges', is_(2))))

        results = self.api._make_leaderboard(one_month_ago - epsilon, now)
        assert_that(results,
                    has_entry(person1, has_entry('badges', is_(1))))
        assert_that(results,
                    has_entry(person4, has_entry('badges', is_(3))))
