import pytest

from tahrir_api.model import Assertion


@pytest.fixture
def initialize_list_assertions(api, dummy_person_id, dummy_issuer_id):
    for unit in range(0, 10):
        tmpbadge = api.add_badge(
            f"AsrtName_{unit}",
            f"AsrtShot_{unit}",
            f"AsrtDesc_{unit}",
            f"AsrtCrit_{unit}",
            dummy_issuer_id,
        )
        api.add_assertion(tmpbadge, "test@tester.com", None, f"link_{unit}")
    return 10


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
    assert award_message.agent_name is None
    assert award_message.usernames == ["test"]
    assert award_message.summary == "test was awarded the badge `TestBadge`"


def test_add_assertion_rejects_legacy_badge(api, dummy_badge_id, dummy_person_id):
    """Test that add_assertion rejects awarding a legacy badge"""
    badge = api.get_badge(dummy_badge_id)
    badge.legacy = True
    api.session.flush()
    with pytest.raises(ValueError, match="legacy badge"):
        api.add_assertion(dummy_badge_id, "test@tester.com", None)
    assert api.assertion_exists(dummy_badge_id, "test@tester.com") is False


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
    assert rank_advance_message.agent_name is None
    assert rank_advance_message.usernames == ["test"]
    assert rank_advance_message.summary == "test's Badges rank changed from None to 1"


def test_remove_assertion_success(api, dummy_badge_id, dummy_person_id):
    """Test successful removal of an assertion"""
    result = api.add_assertion(dummy_badge_id, "test@tester.com", None)
    assert result == ("test@tester.com", dummy_badge_id)
    assert api.assertion_exists(dummy_badge_id, "test@tester.com") is True

    result = api.remove_assertion(dummy_badge_id, "test@tester.com")
    assert result
    assert api.assertion_exists(dummy_badge_id, "test@tester.com") is False

    assertions = api.get_assertions_by_email("test@tester.com")
    assert len(assertions) == 0


def test_remove_assertion_nonexistent_person(api, dummy_badge_id):
    """Test removing assertion for non-existent person returns False"""
    result = api.remove_assertion(dummy_badge_id, "nonexistent@example.com")
    assert result is False


def test_remove_assertion_nonexistent_badge(api, dummy_person_id):
    """Test removing assertion for non-existent badge returns False"""
    result = api.remove_assertion("nonexistent-badge", "test@tester.com")
    assert result is False


def test_remove_assertion_nonexistent_assertion(api, dummy_badge_id, dummy_person_id):
    """Test removing non-existent assertion returns False"""
    result = api.remove_assertion(dummy_badge_id, "test@tester.com")
    assert result is False


@pytest.mark.parametrize(
    "begin, limit, expected_count",
    [
        (None, None, 10),
        (0, 5, 5),
        (5, 5, 5),
        (0, 20, 10),
        (5, None, 5),
        (5, 10, 5),
        (10, 10, 0),
        (None, 0, 0),
        (0, 1, 1),
    ],
)
def test_get_all_assertions(api, initialize_list_assertions, begin, limit, expected_count):
    """Test get_all_assertions with various begin and limit parameters."""
    assertions = list(api.get_all_assertions(begin=begin, limit=limit))

    assert len(assertions) == expected_count
    if len(assertions) > 1:
        assert assertions[0].issued_on >= assertions[1].issued_on

    if begin is not None and begin > 0 and expected_count > 0:
        first_batch = list(api.get_all_assertions(begin=0, limit=expected_count))
        if len(first_batch) == expected_count:
            assert assertions[0].id != first_batch[0].id
