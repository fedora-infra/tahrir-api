import pytest

from tahrir_api.model import Assertion


@pytest.fixture
def dummy_issuer_id(api):
    return api.add_issuer("TestOrigin", "TestName", "TestOrg", "TestContact")


@pytest.fixture
def dummy_badge_id(api, dummy_issuer_id):
    return api.add_badge(
        "TestBadge",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
    )


@pytest.fixture
def dummy_person_id(api):
    return api.add_person("test@tester.com")


def test_add_badges(api, dummy_badge_id):
    assert api.get_badge("testbadge").__str__() == "TestBadge"
    assert api.badge_exists("testbadge") is True


def test_add_team(api):
    api.create_team("TestTeam")

    assert api.team_exists("testteam") is True


def test_add_series(api):
    team_id = api.create_team("TestTeam")

    api.create_series("TestSeries", "A test series", team_id, "test, series")

    assert api.series_exists("testseries") is True


def test_add_milestone(api, dummy_issuer_id):
    team_id = api.create_team("TestTeam")
    series_id = api.create_series("TestSeries", "A test series", team_id, "test, series")

    badge_id_1 = api.add_badge(
        "TestBadge-1",
        "TestImage-2",
        "A test badge for doing 10 unit tests",
        "TestCriteria",
        dummy_issuer_id,
    )

    badge_id_2 = api.add_badge(
        "TestBadge-2",
        "TestImage-2",
        "A test badge for doing 100 unit tests",
        "TestCriteria",
        dummy_issuer_id,
    )

    milestone_id_1 = api.create_milestone(1, badge_id_1, series_id)

    milestone_id_2 = api.create_milestone(2, badge_id_2, series_id)

    assert api.milestone_exists(milestone_id_1) is True
    assert api.milestone_exists(milestone_id_2) is True


def test_add_person(api, dummy_person_id):
    assert api.get_person("test@tester.com").__str__() == "test@tester.com"
    assert api.person_exists("test@tester.com") is True


def test_add_issuer(api, dummy_issuer_id):
    assert api.get_issuer(dummy_issuer_id).__str__() == "TestName"
    assert api.issuer_exists("TestOrigin", "TestName") is True


def test_add_invitation(api, dummy_badge_id, dummy_person_id):
    _id = api.add_invitation(dummy_badge_id, created_by_email="test@tester.com")

    assert api.invitation_exists(_id)
    invitation = api.get_invitation(_id)
    assert api.get_person(id=invitation.created_by).email == "test@tester.com"


def test_add_invitation_no_created_by(api, dummy_badge_id, dummy_person_id):
    with pytest.raises(ValueError):
        api.add_invitation(dummy_badge_id)


def test_last_login(api, callback_calls, dummy_person_id):
    person = api.get_person(dummy_person_id)
    assert not person.last_login
    api.note_login(nickname=person.nickname)
    assert person.last_login

    assert len(callback_calls) == 1
    message = callback_calls[0][0][0]
    assert message.body == {"user": {"username": "test", "badges_user_id": 1}}
    assert message.agent_name == "test"
    assert message.summary == "test logged into badges for the first time"


def test_add_assertion(api, callback_calls, dummy_badge_id, dummy_person_id):
    api.add_assertion(dummy_badge_id, "test@tester.com", None, "link")
    assert api.assertion_exists(dummy_badge_id, "test@tester.com")

    badge = api.get_badge(dummy_badge_id)
    assert badge.assertions[0].issued_for == "link"
    assert api.get_assertions_by_badge(dummy_badge_id)[0].__str__() == "TestBadge<->test@tester.com"

    # Ensure that we would have published a fedmsg messages for that.
    assert len(callback_calls) == 1

    award_message = callback_calls[0][0][0]

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


@pytest.mark.parametrize("test_email", ["test@tester.com", "Test@Tester.Com"])
def test_get_assertions_by_email(api, callback_calls, dummy_badge_id, dummy_person_id, test_email):
    api.add_assertion(dummy_badge_id, "test@tester.com", None, "link")
    # This should be case-insensitive
    assertions = api.get_assertions_by_email(person_email=test_email)
    assert len(assertions) == 1
    assert str(assertions[0]) == "TestBadge<->test@tester.com"


def test_adjust_ranks(api, callback_calls, dummy_badge_id, dummy_person_id):
    person = api.get_person(dummy_person_id)
    assertion = Assertion(
        badge_id=dummy_badge_id,
        person_id=person.id,
        issued_for="link",
    )
    api.session.add(assertion)
    api.session.flush()

    api.adjust_ranks(person)

    # Ensure that we would have published a fedmsg messages for that.
    assert len(callback_calls) == 1
    rank_advance_message = callback_calls[0][0][0]
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


def test_get_badges_from_tags(api, dummy_issuer_id):
    # Badge tagged with "test"
    api.add_badge(
        "TestBadgeA",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="test",
    )

    # Badge tagged with "tester"
    api.add_badge(
        "TestBadgeB",
        "TestImage",
        "A second test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tester",
    )

    # Badge tagged with both "test" and "tester"
    api.add_badge(
        "TestBadgeC",
        "TestImage",
        "A third test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="test, tester",
    )

    tags = ["test", "tester"]
    badges_any = api.get_badges_from_tags(tags, match_all=False)
    assert len(badges_any) == 3
    badges_all = api.get_badges_from_tags(tags, match_all=True)
    assert len(badges_all) == 1
