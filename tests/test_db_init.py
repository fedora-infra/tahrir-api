from tahrir_api import TahrirDatabase
try:
    from subprocess import check_output
except:
    import subprocess
    def check_output(cmd):
        return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]

class TestDBInit(object):

    def setUp(self):
        check_output(['rm', '-rf', '/tmp/testdb.db'])
        check_output(['touch', '/tmp/testdb.db'])
        check_output(["rm", "/tmp/test.ini"])
        sqlalchemy_uri = "sqlite:////temp/testdb.db"
        with file("/tmp/test.ini",'w') as f:
            f.write("[app:pyramid]\nsqlalchemy.url = {0}".format(sqlalchemy_uri))
        check_output(["initialize_tahrir_db", "/tmp/test.ini"])
        self.api = TahrirDatabase(sqlalchemy_uri)

    def test_AddBadges(self):
        self.api.add_badge(
                "TestBadge",
                "TestImage",
                "A test badge for doing unit tests",
                "TestCriteria",
                1337
        )

        assert self.api.badge_exists("testbadge") == True

    def test_AddPerson(self):
        self.api.add_person(7331, "test@tester.com")
        assert self.api.person_exists("test@tester.com") == True

    def test_AddIssuer(self):
        _id = self.api.add_issuer(
                "TestOrigin",
                "TestName",
                "TestOrg",
                "TestContact"
        )
        assert self.api.issuer_exists(_id) == True

