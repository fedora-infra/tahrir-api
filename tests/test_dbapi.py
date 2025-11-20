from datetime import datetime, timedelta

import pytest

from tahrir_api.model import Assertion, Authorization, Badge, Milestone, Person, Series, Team


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
    assert award_message.agent_name is None
    assert award_message.usernames == ["test"]
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
    assert rank_advance_message.agent_name is None
    assert rank_advance_message.usernames == ["test"]
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
    "kwargs",
    [
        # Test individual field updates
        {"name": "UpdatedName"},
        {"image": "UpdatedImage"},
        {"description": "Updated description"},
        {"criteria": "Updated criteria"},
        {"tags": "updated, tags"},
        {"tags": "updated, tags,"},
        # Test multiple field updates
        {
            "name": "MultiUpdate",
            "image": "MultiImage",
            "description": "Multi description",
            "criteria": "Multi criteria",
            "tags": "multi, tags",
        },
        # Test empty update
        {},
    ],
)
def test_update_badge(api, dummy_badge_id, kwargs):
    """Test updating badge"""
    # Obtain
    existing_badge = api.get_badge(dummy_badge_id)

    # Create
    expected_name = kwargs.get("name", existing_badge.name)
    expected_image = kwargs.get("image", existing_badge.image)
    expected_description = kwargs.get("description", existing_badge.description)
    expected_criteria = kwargs.get("criteria", existing_badge.criteria)

    # Handle
    if "tags" in kwargs:
        tags = kwargs["tags"]
        expected_tags = tags + "," if tags and not tags.endswith(",") else tags
    else:
        expected_tags = existing_badge.tags

    # Update
    api.update_badge(dummy_badge_id, **kwargs)

    # Obtain
    updated_badge = api.get_badge(dummy_badge_id)

    # Verify
    assert updated_badge.name == expected_name
    assert updated_badge.image == expected_image
    assert updated_badge.description == expected_description
    assert updated_badge.criteria == expected_criteria
    assert updated_badge.tags == expected_tags


def test_update_badge_nonexistent(api):
    """Test updating badge which are non-existent and returns False"""
    result = api.update_badge("nonexistent_badge_id", name="UpdatedName")
    assert result is False


def test_update_badge_invalid_fields(api, dummy_badge_id):
    """Test updating badge with invalid fields and raises KeyError"""
    with pytest.raises(KeyError, match="Invalid fields"):
        api.update_badge(dummy_badge_id, invalid_field="value")


@pytest.mark.parametrize(
    "identifier_type,update_data",
    [
        ("email", {"avatar": "test@test-libravatar.com"}),
        ("id", {"bio": "Updated bio via ID"}),
        ("nickname", {"website": "https://nickname-example.com"}),
    ],
)
def test_update_person_by_identifier(api, dummy_person_id, identifier_type, update_data):
    """Test updating person profile fields using different identification methods."""
    person = api.get_person("test@tester.com")
    assert person.website is None
    assert person.bio is None
    assert person._avatar is None

    if identifier_type == "email":
        update_args = {"person_email": "test@tester.com"}
    elif identifier_type == "id":
        update_args = {"id": person.id}
    else:
        update_args = {"nickname": person.nickname}

    lookup_args = update_args.copy()
    update_args.update(update_data)
    result = api.update_person(**update_args)
    assert result.email == "test@tester.com"

    # Verify the updated fields are present in the returned object
    for dictname, expected in update_data.items():
        formname = "_avatar" if dictname == "avatar" else dictname
        assert getattr(result, formname) == expected

    # Also verify by fetching fresh from database
    updated_person = api.get_person(**lookup_args)
    for field, expected_value in update_data.items():
        actual_field = "_avatar" if field == "avatar" else field
        assert getattr(updated_person, actual_field) == expected_value


def test_update_person_none_values(api, dummy_person_id):
    """Test that None values don't overwrite existing data."""
    # Set initial values
    api.update_person(
        person_email="test@tester.com",
        website="https://example.com",
        bio="Existing bio",
        avatar="test@test-libravatar.com",
    )
    result = api.update_person(person_email="test@tester.com", website=None, bio=None, avatar=None)

    # Verify the returned object still has the original values (not overwritten by None)
    assert result.email == "test@tester.com"
    assert result.website == "https://example.com"
    assert result.bio == "Existing bio"
    assert result._avatar == "test@test-libravatar.com"

    # Also verify by fetching fresh from database
    person = api.get_person("test@tester.com")
    assert person.website == "https://example.com"
    assert person.bio == "Existing bio"
    assert person._avatar == "test@test-libravatar.com"


@pytest.mark.parametrize(
    "identifier_type,identifier_value",
    [("email", "nonexistent@example.com"), ("id", 999999), ("nickname", "nonexistent_user")],
)
def test_update_person_nonexistent(api, identifier_type, identifier_value):
    """Test updating a person that doesn't exist should return False."""
    if identifier_type == "email":
        update_args = {"person_email": identifier_value}
    elif identifier_type == "id":
        update_args = {"id": identifier_value}
    else:
        update_args = {"nickname": identifier_value}

    update_args["website"] = "https://example.com"
    result = api.update_person(**update_args)
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


def test_get_team(api):
    """Test retrieving a team by ID"""
    team = Team(id="test-team", name="Test Team")
    api.session.add(team)
    api.session.flush()

    received_team = api.get_team("test-team")
    assert received_team is not None
    assert received_team.name == "Test Team"
    assert received_team.id == "test-team"

    absented_team = api.get_team("absented-team")
    assert absented_team is None


def test_get_series_from_team(api):
    """Test retrieving series from a team"""
    team = Team(id="test-team", name="Test Team")
    api.session.add(team)
    api.session.flush()

    series = api.get_series_from_team("test-team")
    assert series == []

    series_a = Series(
        id="test-series-alpha",
        name="Test Series Alpha",
        description="Alpha test series",
        team_id="test-team",
        tags="test, series",
    )
    series_b = Series(
        id="test-series-bravo",
        name="Test Series Bravo",
        description="Bravo test series",
        team_id="test-team",
        tags="test, series",
    )
    api.session.add(series_a)
    api.session.add(series_b)
    api.session.flush()

    series = api.get_series_from_team("test-team")
    assert len(series) == 2

    series_names = [s.name for s in series]
    assert "Test Series Alpha" in series_names
    assert "Test Series Bravo" in series_names

    absented_series = api.get_series_from_team("absented-team")
    assert absented_series is None


def test_get_badges_from_team(api, dummy_issuer_id):
    """Test retrieving badges from a team via series and milestones"""
    team = Team(id="test-team", name="Test Team")
    api.session.add(team)
    api.session.flush()

    badges = api.get_badges_from_team("test-team")
    assert badges == []

    series = Series(
        id="test-series",
        name="Test Series",
        description="Test series",
        team_id="test-team",
        tags="test, series",
    )
    api.session.add(series)
    api.session.flush()

    badges = api.get_badges_from_team("test-team")
    assert badges == []

    badge_a = Badge(
        id="test-badge-alpha",
        name="Test Badge Alpha",
        image="TestImageAlpha",
        description="Test Badge Alpha",
        criteria="TestCriteriaAlpha",
        issuer_id=dummy_issuer_id,
    )
    badge_b = Badge(
        id="test-badge-bravo",
        name="Test Badge Bravo",
        image="TestImageBravo",
        description="Test Badge Bravo",
        criteria="TestCriteriaBravo",
        issuer_id=dummy_issuer_id,
    )
    api.session.add(badge_a)
    api.session.add(badge_b)
    api.session.flush()

    milestone_a = Milestone(position=1, badge_id="test-badge-alpha", series_id="test-series")
    milestone_b = Milestone(position=2, badge_id="test-badge-bravo", series_id="test-series")
    api.session.add(milestone_a)
    api.session.add(milestone_b)
    api.session.flush()

    badges = api.get_badges_from_team("test-team")
    assert badges is not None
    assert len(badges) == 2

    badge_names = [b.name for b in badges]
    assert "Test Badge Alpha" in badge_names
    assert "Test Badge Bravo" in badge_names

    absented_badges = api.get_badges_from_team("absented-team")
    assert absented_badges is None


def test_get_series_existing(api):
    """Test getting an existing series by ID."""
    team = Team(id="test-team", name="Test Team")
    api.session.add(team)
    api.session.flush()
    series = Series(
        id="test-series",
        name="Test Series",
        description="A test series for unit testing",
        tags="test, series",
        team_id="test-team",
    )
    api.session.add(series)
    api.session.flush()

    retrieved_series = api.get_series("test-series")
    assert retrieved_series is not None
    assert retrieved_series.id == "test-series"
    assert retrieved_series.name == "Test Series"
    assert retrieved_series.description == "A test series for unit testing"
    assert retrieved_series.tags == "test, series"


def test_get_series_nonexistent(api):
    """Test getting a non-existent series returns None."""
    series = api.get_series("absented-series")
    assert series is None


def test_get_all_series_empty(api):
    """Test getting all series when none exist."""
    direct_count = api.session.query(Series).count()
    assert direct_count == 0
    series_query = api.get_all_series()
    series_list = list(series_query)
    assert len(series_list) == 0
