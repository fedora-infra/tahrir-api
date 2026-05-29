from datetime import datetime, timedelta

import pytest


def test_add_invitation(api, dummy_badge_id, dummy_person_id):
    _id = api.add_invitation(dummy_badge_id, created_by_email="test@tester.com")

    assert api.invitation_exists(_id)
    invitation = api.get_invitation(_id)
    assert api.get_person(id=invitation.created_by).email == "test@tester.com"


def test_add_invitation_no_created_by(api, dummy_badge_id, dummy_person_id):
    with pytest.raises(ValueError):
        api.add_invitation(dummy_badge_id)


def test_add_invitation_rejects_legacy_badge(api, dummy_badge_id, dummy_person_id):
    """Test that add_invitation rejects creating an invitation for a legacy badge"""
    badge = api.get_badge(dummy_badge_id)
    badge.legacy = True
    api.session.flush()

    with pytest.raises(ValueError, match="legacy badge"):
        api.add_invitation(dummy_badge_id, created_by_email="test@tester.com")


def test_expire_invitation(api, dummy_badge_id, dummy_person_id):
    # Create
    future_time = datetime.now() + timedelta(hours=2)
    _id = api.add_invitation(
        dummy_badge_id, created_by_email="test@tester.com", expires_on=future_time
    )

    # Verify
    assert api.invitation_exists(_id)
    invitation = api.get_invitation(_id)
    assert not invitation.expired

    # Expire
    result = api.expire_invitation(_id)
    assert result is True

    # Verify
    expired_invitation = api.get_invitation(_id)
    assert expired_invitation.expired

    # Absent
    result = api.expire_invitation("non-existent-id")
    assert result is False
