from __future__ import unicode_literals

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DBSession, DeclarativeBase
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


class TestDBInit(object):

    def setUp(self):
        check_output(['touch', 'testdb.db'])
        sqlalchemy_uri = "sqlite:///testdb.db"
        engine = create_engine(sqlalchemy_uri)
        DBSession.configure(bind=engine)
        DeclarativeBase.metadata.create_all(engine)

        self.callback_calls = []
        self.api = TahrirDatabase(
            sqlalchemy_uri,
            notification_callback=self.callback)

    def callback(self, *args, **kwargs):
        self.callback_calls.append((args, kwargs))

    def test_add_badges(self):
        self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            1337
        )

        assert self.api.badge_exists("testbadge") is True

    def test_add_team(self):
        self.api.create_team("TestTeam")

        assert self.api.team_exists("testteam") is True

    def test_add_series(self):
        team_id = self.api.create_team("TestTeam")

        self.api.create_series("TestSeries",
                               "A test series",
                               team_id,
                               "test, series")

        assert self.api.series_exists("testseries") is True

    def test_add_milestone(self):
        team_id = self.api.create_team("TestTeam")

        series_id = self.api.create_series("TestSeries",
                                           "A test series",
                                           team_id,
                                           "test, series")

        badge_id_1 = self.api.add_badge(
            "TestBadge-1",
            "TestImage-2",
            "A test badge for doing 10 unit tests",
            "TestCriteria",
            1337
        )

        badge_id_2 = self.api.add_badge(
            "TestBadge-2",
            "TestImage-2",
            "A test badge for doing 100 unit tests",
            "TestCriteria",
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
        self.api.add_person("test@tester.com")
        assert self.api.person_exists("test@tester.com") is True

    def test_add_issuer(self):
        _id = self.api.add_issuer(
            "TestOrigin",
            "TestName",
            "TestOrg",
            "TestContact"
        )
        assert self.api.issuer_exists("TestOrigin", "TestName") is True

    def test_add_invitation(self):
        badge_id = self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            1337
        )
        _id = self.api.add_invitation(
            badge_id,
        )

        assert self.api.invitation_exists(_id)

    def test_last_login(self):
        email = "test@tester.com"
        person_id = self.api.add_person(email)
        person = self.api.get_person(person_id)
        assert not person.last_login
        self.api.note_login(nickname=person.nickname)
        assert person.last_login

    def test_add_assertion(self):
        issuer_id = self.api.add_issuer(
            "TestOrigin",
            "TestName",
            "TestOrg",
            "TestContact"
        )
        badge_id = self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
        )
        email = "test@tester.com"
        person_id = self.api.add_person(email)
        assertion_id = self.api.add_assertion(badge_id, email, None, 'link')
        assert self.api.assertion_exists(badge_id, email)

        badge = self.api.get_badge(badge_id)
        assert badge.assertions[0].issued_for == 'link'

        # Ensure that we would have published two fedmsg messages for that.
        assert len(self.callback_calls) == 2

        # Ensure that the first message had a 'badge_id' in the message.
        assert 'badge_id' in self.callback_calls[0][1]['msg']['badge']

    def test_get_badges_from_tags(self):
        issuer_id = self.api.add_issuer(
            "TestOrigin",
            "TestName",
            "TestOrg",
            "TestContact"
        )

        # Badge tagged with "test"
        self.api.add_badge(
            "TestBadgeA",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="test"
        )

        # Badge tagged with "tester"
        self.api.add_badge(
            "TestBadgeB",
            "TestImage",
            "A second test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="tester"
        )

        # Badge tagged with both "test" and "tester"
        self.api.add_badge(
            "TestBadgeC",
            "TestImage",
            "A third test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="test, tester"
        )

        tags = ['test', 'tester']
        badges_any = self.api.get_badges_from_tags(tags, match_all=False)
        assert len(badges_any) == 3
        badges_all = self.api.get_badges_from_tags(tags, match_all=True)
        assert len(badges_all) == 1

    def tearDown(self):
        check_output(['rm', 'testdb.db'])
        self.callback_calls = []
