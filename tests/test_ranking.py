import datetime

import pytest

from tahrir_api.model import Assertion


now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days=1)
one_week_ago = now - datetime.timedelta(days=7)
one_month_ago = now - datetime.timedelta(weeks=4)


def assert_in(member, container):
    """Just like assertTrue(a in b), but with a nicer default message."""
    if member not in container:
        raise AssertionError(f"{member} not found in {container}")


@pytest.fixture
def test_data(api):
    issuer_id = api.add_issuer("TestOrigin", "TestName", "TestOrg", "TestContact")
    badge_id_1 = api.add_badge(
        "TestBadge1",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        issuer_id,
    )
    badge_id_2 = api.add_badge(
        "TestBadge2",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        issuer_id,
    )
    badge_id_3 = api.add_badge(
        "TestBadge3",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        issuer_id,
    )
    email_1 = "test_1@tester.com"
    api.add_person(email_1)
    email_2 = "test_2@tester.com"
    api.add_person(email_2)
    email_3 = "test_3@tester.com"
    api.add_person(email_3)
    email_4 = "test_4@tester.com"
    api.add_person(email_4)
    return {
        "badge_1": badge_id_1,
        "badge_2": badge_id_2,
        "badge_3": badge_id_3,
        "email_1": email_1,
        "email_2": email_2,
        "email_3": email_3,
        "email_4": email_4,
    }


def test_ranking_simple(api, test_data):
    api.add_assertion(test_data["badge_1"], test_data["email_1"], None)

    api.add_assertion(test_data["badge_1"], test_data["email_4"], None)
    api.add_assertion(test_data["badge_2"], test_data["email_4"], None)
    api.add_assertion(test_data["badge_3"], test_data["email_4"], None)

    person1 = api.get_person("test_1@tester.com")
    person4 = api.get_person("test_4@tester.com")

    assert person1.rank == 2
    assert person4.rank == 1


def test_ranking_tie(api, test_data):
    api.add_assertion(test_data["badge_1"], test_data["email_1"], None)

    api.add_assertion(test_data["badge_1"], test_data["email_2"], None)
    api.add_assertion(test_data["badge_2"], test_data["email_2"], None)

    api.add_assertion(test_data["badge_1"], test_data["email_3"], None)
    api.add_assertion(test_data["badge_2"], test_data["email_3"], None)

    api.add_assertion(test_data["badge_1"], test_data["email_4"], None)
    api.add_assertion(test_data["badge_2"], test_data["email_4"], None)
    api.add_assertion(test_data["badge_3"], test_data["email_4"], None)

    person1 = api.get_person("test_1@tester.com")
    person2 = api.get_person("test_2@tester.com")
    person3 = api.get_person("test_3@tester.com")
    person4 = api.get_person("test_4@tester.com")

    assert person1.rank == 4
    assert person2.rank == 2
    assert person3.rank == 2
    assert person4.rank == 1


def test_ranking_preexisting(api, test_data):
    """Test that rank updating works for pre-existant users"""
    person1 = api.get_person("test_1@tester.com")
    new_assertion1 = Assertion(badge_id=test_data["badge_1"], person_id=person1.id)
    api.session.add(new_assertion1)
    new_assertion2 = Assertion(badge_id=test_data["badge_2"], person_id=person1.id)
    api.session.add(new_assertion2)
    api.session.flush()

    # For persons who existed *before* we added cached ranks, they should
    # have a null-rank.
    assert person1.rank is None

    # But once *anyone* else gets a badge, old ranks should be updated too.
    api.add_assertion(test_data["badge_1"], test_data["email_2"], None)
    assert person1.rank == 1

    person2 = api.get_person("test_2@tester.com")
    assert person2.rank == 2

    # but people with no badges should still be null ranked.
    person3 = api.get_person("test_3@tester.com")
    assert person3.rank is None


def test_ranking_with_time_limits(api, test_data):
    api.add_assertion(test_data["badge_1"], test_data["email_1"], yesterday)

    api.add_assertion(test_data["badge_1"], test_data["email_4"], yesterday)
    api.add_assertion(test_data["badge_2"], test_data["email_4"], one_week_ago)
    api.add_assertion(test_data["badge_3"], test_data["email_4"], one_month_ago)

    person1 = api.get_person("test_1@tester.com")
    person4 = api.get_person("test_4@tester.com")

    epsilon = datetime.timedelta(hours=1)

    results = api._make_leaderboard(yesterday - epsilon, now)
    assert results[person1]["badges"] == 1
    assert results[person4]["badges"] == 1

    results = api._make_leaderboard(one_week_ago - epsilon, now)
    assert results[person1]["badges"] == 1
    assert results[person4]["badges"] == 2

    results = api._make_leaderboard(one_month_ago - epsilon, now)
    assert results[person1]["badges"] == 1
    assert results[person4]["badges"] == 3
