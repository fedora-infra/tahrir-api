import unittest

from sqlalchemy import create_engine

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DeclarativeBase

try:
    from subprocess import check_output as _check_output

    def check_output(cmd):
        try:
            return _check_output(cmd)
        except Exception:
            return None

except Exception:
    import subprocess

    def check_output(cmd):
        try:
            return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
        except Exception:
            return None


class TestDBInit(unittest.TestCase):
    def setUp(self):
        check_output(["touch", "testdb.db"])
        sqlalchemy_uri = "sqlite:///testdb.db"
        engine = create_engine(sqlalchemy_uri)
        DeclarativeBase.metadata.create_all(engine)

        self.callback_calls = []
        self.api = TahrirDatabase(sqlalchemy_uri, notification_callback=self.callback)

    def callback(self, *args, **kwargs):
        self.callback_calls.append((args, kwargs))

    def test_add_badges(self):
        self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            1337,
        )
        assert self.api.get_badge("testbadge").__str__() == "TestBadge"
        assert self.api.badge_exists("testbadge") is True

    def test_add_team(self):
        self.api.create_team("TestTeam")

        assert self.api.team_exists("testteam") is True

    def test_add_series(self):
        team_id = self.api.create_team("TestTeam")

        self.api.create_series("TestSeries", "A test series", team_id, "test, series")

        assert self.api.series_exists("testseries") is True

    def test_add_milestone(self):
        team_id = self.api.create_team("TestTeam")

        series_id = self.api.create_series("TestSeries", "A test series", team_id, "test, series")

        badge_id_1 = self.api.add_badge(
            "TestBadge-1",
            "TestImage-2",
            "A test badge for doing 10 unit tests",
            "TestCriteria",
            1337,
        )

        badge_id_2 = self.api.add_badge(
            "TestBadge-2",
            "TestImage-2",
            "A test badge for doing 100 unit tests",
            "TestCriteria",
            1337,
        )

        milestone_id_1 = self.api.create_milestone(1, badge_id_1, series_id)

        milestone_id_2 = self.api.create_milestone(2, badge_id_2, series_id)

        assert self.api.milestone_exists(milestone_id_1) is True
        assert self.api.milestone_exists(milestone_id_2) is True

    def test_add_person(self):
        self.api.add_person("test@tester.com")
        assert self.api.get_person("test@tester.com").__str__() == "test@tester.com"
        assert self.api.person_exists("test@tester.com") is True

    def test_add_issuer(self):
        _id = self.api.add_issuer("TestOrigin", "TestName", "TestOrg", "TestContact")
        assert self.api.get_issuer(_id).__str__() == "TestName"
        assert self.api.issuer_exists("TestOrigin", "TestName") is True

    def test_add_invitation(self):
        badge_id = self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            1337,
        )
        _id = self.api.add_invitation(badge_id)

        assert self.api.invitation_exists(_id)

    def test_last_login(self):
        email = "test@tester.com"
        person_id = self.api.add_person(email)
        person = self.api.get_person(person_id)
        assert not person.last_login
        self.api.note_login(nickname=person.nickname)
        assert person.last_login

        assert len(self.callback_calls) == 1
        message = self.callback_calls[0][0][0]
        assert message.body == {"user": {"username": "test", "badges_user_id": 1}}
        assert message.agent_name == "test"
        assert message.summary == "test logged into badges for the first time"

    def test_add_assertion(self):
        issuer_id = self.api.add_issuer("TestOrigin", "TestName", "TestOrg", "TestContact")
        badge_id = self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
        )
        email = "test@tester.com"
        self.api.add_person(email)
        self.api.add_assertion(badge_id, email, None, "link")
        assert self.api.assertion_exists(badge_id, email)

        badge = self.api.get_badge(badge_id)
        assert badge.assertions[0].issued_for == "link"
        assert (
            self.api.get_assertions_by_badge(badge_id)[0].__str__() == "TestBadge<->test@tester.com"
        )

        # Ensure that we would have published two fedmsg messages for that.
        assert len(self.callback_calls) == 2

        award_message = self.callback_calls[0][0][0]
        rank_advance_message = self.callback_calls[1][0][0]

        assert award_message.body == {
            "badge": {
                "name": "TestBadge",
                "description": "A test badge for doing unit tests",
                "image_url": "TestImage",
                "badge_id": "testbadge",
            },
            "user": {"username": "test", "badges_user_id": 1},
        }
        assert award_message.agent_name == "test"
        assert award_message.summary == "test was awarded the badge `TestBadge`"

        assert rank_advance_message.body == {
            "person": {
                "email": "test@tester.com",
                "id": 1,
                "nickname": "test",
                "website": None,
                "bio": None,
                "rank": 1,
            },
            "old_rank": None,
        }
        assert rank_advance_message.agent_name == "test"
        assert rank_advance_message.summary == "test's Badges rank changed from None to 1"

    def test_get_badges_from_tags(self):
        issuer_id = self.api.add_issuer("TestOrigin", "TestName", "TestOrg", "TestContact")

        # Badge tagged with "test"
        self.api.add_badge(
            "TestBadgeA",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="test",
        )

        # Badge tagged with "tester"
        self.api.add_badge(
            "TestBadgeB",
            "TestImage",
            "A second test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="tester",
        )

        # Badge tagged with both "test" and "tester"
        self.api.add_badge(
            "TestBadgeC",
            "TestImage",
            "A third test badge for doing unit tests",
            "TestCriteria",
            issuer_id,
            tags="test, tester",
        )

        tags = ["test", "tester"]
        badges_any = self.api.get_badges_from_tags(tags, match_all=False)
        assert len(badges_any) == 3
        badges_all = self.api.get_badges_from_tags(tags, match_all=True)
        assert len(badges_all) == 1

    def tearDown(self):
        check_output(["rm", "testdb.db"])
        self.callback_calls = []
