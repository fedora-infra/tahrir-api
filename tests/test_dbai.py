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

        self.api = TahrirDatabase(sqlalchemy_uri)

    def test_add_badges(self):
        self.api.add_badge(
            "TestBadge",
            "TestImage",
            "A test badge for doing unit tests",
            "TestCriteria",
            1337
        )

        assert self.api.badge_exists("testbadge") is True

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
        assertion_id = self.api.add_assertion(badge_id, email, None)
        assert self.api.assertion_exists(badge_id, email)

    def tearDown(self):
        check_output(['rm', 'testdb.db'])
