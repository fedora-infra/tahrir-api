from __future__ import unicode_literals

from nose.tools import eq_

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DBSession, DeclarativeBase, Assertion
from sqlalchemy import create_engine


try:
    from subprocess import check_output as _check_output

    def check_output(cmd):
        try:
            return _check_output(cmd)
        except:
            return None
except:
    import subprocess

    def check_output(cmd):
        try:
            return subprocess.Popen(
                cmd, stdout=subprocess.PIPE).communicate()[0]
        except:
            return None


import datetime
now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days=1)
one_week_ago = now - datetime.timedelta(days=7)
one_month_ago = now - datetime.timedelta(weeks=4)


def assert_in(member, container):
    """ Just like assertTrue(a in b), but with a nicer default message. """
    if member not in container:
        raise AssertionError('%r not found in %r' % (member, container))


class TestRanking(object):

    def setUp(self):
        check_output(['touch', 'testdb.db'])
        sqlalchemy_uri = "sqlite:///testdb.db"
        engine = create_engine(sqlalchemy_uri)
        DBSession.configure(bind=engine)
        DeclarativeBase.metadata.create_all(engine)

        self.api = TahrirDatabase(sqlalchemy_uri)
        self._create_test_data()

    def tearDown(self):
        check_output(['rm', 'testdb.db'])

    def _create_test_data(self):
        issuer_id = self.api.add_issuer(
            "TestOrigin",
            "TestName",
            "TestOrg",
            "TestContact"
        )
        self.badge_id_1 = self.api.add_badge(
            "TestBadge1",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
        )
        self.badge_id_2 = self.api.add_badge(
            "TestBadge2",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
        )
        self.badge_id_3 = self.api.add_badge(
            "TestBadge3",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
        )
        self.email_1 = "test_1@tester.com"
        person_id_1 = self.api.add_person(self.email_1)
        self.email_2 = "test_2@tester.com"
        person_id_2 = self.api.add_person(self.email_2)
        self.email_3 = "test_3@tester.com"
        person_id_3 = self.api.add_person(self.email_3)
        self.email_4 = "test_4@tester.com"
        person_id_4 = self.api.add_person(self.email_4)

    def test_ranking_simple(self):
        self.api.add_assertion(self.badge_id_1, self.email_1, None)

        self.api.add_assertion(self.badge_id_1, self.email_4, None)
        self.api.add_assertion(self.badge_id_2, self.email_4, None)
        self.api.add_assertion(self.badge_id_3, self.email_4, None)

        person1 = self.api.get_person("test_1@tester.com")
        person4 = self.api.get_person("test_4@tester.com")

        eq_(person1.rank, 2)
        eq_(person4.rank, 1)

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

        eq_(person1.rank, 4)
        eq_(person2.rank, 2)
        eq_(person3.rank, 2)
        eq_(person4.rank, 1)

    def test_ranking_preexisting(self):
        """ Test that rank updating works for pre-existant users """
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
        eq_(person1.rank, None)

        # But once *anyone* else gets a badge, old ranks should be updated too.
        self.api.add_assertion(self.badge_id_1, self.email_2, None)
        eq_(person1.rank, 1)

        person2 = self.api.get_person("test_2@tester.com")
        eq_(person2.rank, 2)

        # but people with no badges should still be null ranked.
        person3 = self.api.get_person("test_3@tester.com")
        eq_(person3.rank, None)

    def test_ranking_with_time_limits(self):
        self.api.add_assertion(self.badge_id_1, self.email_1, yesterday)

        self.api.add_assertion(self.badge_id_1, self.email_4, yesterday)
        self.api.add_assertion(self.badge_id_2, self.email_4, one_week_ago)
        self.api.add_assertion(self.badge_id_3, self.email_4, one_month_ago)

        person1 = self.api.get_person("test_1@tester.com")
        person4 = self.api.get_person("test_4@tester.com")

        epsilon = datetime.timedelta(hours=1)

        results = self.api._make_leaderboard(yesterday - epsilon, now)
        eq_(results[person1]['badges'], 1)
        eq_(results[person4]['badges'], 1)

        results = self.api._make_leaderboard(one_week_ago - epsilon, now)
        eq_(results[person1]['badges'], 1)
        eq_(results[person4]['badges'], 2)

        results = self.api._make_leaderboard(one_month_ago - epsilon, now)
        eq_(results[person1]['badges'], 1)
        eq_(results[person4]['badges'], 3)
