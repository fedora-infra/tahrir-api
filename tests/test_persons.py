import pytest


def test_add_person(api, dummy_person_id):
    assert api.get_person("test@tester.com").__str__() == "test@tester.com"
    assert api.person_exists("test@tester.com") is True


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
    [
        ("email", "nonexistent@example.com"),
        ("id", 999999),
        ("nickname", "nonexistent_user"),
    ],
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
    "search_string, expected_total, expected_nicknames",
    [
        ("alice", 1, ["alice_wonder"]),
        ("test", 2, ["dave_test", "diana_test"]),
        ("zzznomatch", 0, []),
        ("uppercase", 1, ["UpperCase"]),
    ],
)
def test_get_persons_by_nickname_search(api, search_string, expected_total, expected_nicknames):
    api.add_person("alice@test.com", nickname="alice_wonder")
    api.add_person("dave@test.com", nickname="dave_test")
    api.add_person("diana@test.com", nickname="diana_test")
    api.add_person("upper@test.com", nickname="UpperCase")
    result = api.get_persons_by_nickname(search_string)
    assert result["total"] == expected_total
    nicknames = [p.nickname for p in result["users"]]
    assert nicknames == expected_nicknames


@pytest.mark.parametrize(
    "begin, limit, expected_count",
    [
        (0, 2, 2),
        (2, 2, 2),
        (4, 2, 1),
    ],
)
def test_get_persons_by_nickname_pagination(api, begin, limit, expected_count):
    for i in range(5):
        api.add_person(f"user{i}@test.com", nickname=f"user_{i}")
    result = api.get_persons_by_nickname("user", begin=begin, limit=limit)
    assert len(result["users"]) == expected_count
    assert result["total"] == 5
    assert result["begin"] == begin
    assert result["limit"] == limit
