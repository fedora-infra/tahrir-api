import pytest

from tahrir_api.model import Authorization, Person


def test_delete_authorization_success(api, dummy_badge_id, dummy_person_id):
    """Test successful deletion of an authorization"""
    person = api.session.query(Person).filter_by(email="test@tester.com").one()
    authorization = Authorization(badge_id=dummy_badge_id, person_id=person.id)
    api.session.add(authorization)
    api.session.flush()

    auth_count = (
        api.session.query(Authorization)
        .filter_by(badge_id=dummy_badge_id, person_id=person.id)
        .count()
    )
    assert auth_count == 1

    result = api.delete_authorization(dummy_badge_id, "test@tester.com")

    auth_count = (
        api.session.query(Authorization)
        .filter_by(badge_id=dummy_badge_id, person_id=person.id)
        .count()
    )

    assert result == ("test@tester.com", dummy_badge_id)
    assert auth_count == 0


def test_delete_authorization_nonexistent_person(api, dummy_badge_id):
    """Test deleting authorization for non-existent person returns False"""
    result = api.delete_authorization(dummy_badge_id, "nonexistent@example.com")
    assert result is False


def test_delete_authorization_nonexistent_authorization(api, dummy_badge_id, dummy_person_id):
    """Test deleting non-existent authorization returns False"""
    person = api.session.query(Person).filter_by(email="test@tester.com").one()
    auth_count = (
        api.session.query(Authorization)
        .filter_by(badge_id=dummy_badge_id, person_id=person.id)
        .count()
    )
    assert auth_count == 0

    result = api.delete_authorization(dummy_badge_id, "test@tester.com")
    assert result is False


@pytest.mark.parametrize(
    "badge_id,email,should_succeed",
    [
        ("testbadge", "test@tester.com", True),
        ("testbadge", "nonexistent@example.com", False),
        ("nonexistent-badge", "test@tester.com", False),
    ],
)
def test_add_authorization(api, dummy_badge_id, dummy_person_id, badge_id, email, should_succeed):
    """Test adding authorization with various badge and person combinations"""
    result = api.add_authorization(badge_id, email)

    if should_succeed:
        assert result == (email, badge_id)
        assert api.authorization_exists(badge_id, email) is True
    else:
        assert result is False
        assert api.authorization_exists(badge_id, email) is False


def test_add_authorization_rejects_legacy_badge(api, dummy_badge_id, dummy_person_id):
    """Test that add_authorization rejects authorizing a legacy badge"""

    badge = api.get_badge(dummy_badge_id)
    badge.legacy = True
    api.session.flush()

    with pytest.raises(ValueError, match="legacy badge"):
        api.add_authorization(dummy_badge_id, "test@tester.com")
    assert api.authorization_exists(dummy_badge_id, "test@tester.com") is False
