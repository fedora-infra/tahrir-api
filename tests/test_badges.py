import pytest

from tahrir_api.model import Tag


@pytest.fixture
def search_test_badges(api, dummy_issuer_id):
    api.add_badge(
        name="Python Expert",
        image="python_expert.png",
        desc="Badge for Python programming excellence",
        criteria="Complete 100 Python exercises",
        issuer_id=dummy_issuer_id,
        tags=["python", "programming", "expert"],
    )
    api.add_badge(
        name="JavaScript Ninja",
        image="js_ninja.png",
        desc="Master the JavaScript language and frameworks",
        criteria="Build 5 JavaScript projects",
        issuer_id=dummy_issuer_id,
        tags=["javascript", "web", "frontend"],
    )
    api.add_badge(
        name="Frontend Master",
        image="frontend.png",
        desc="Expert web developer with full-stack capabilities",
        criteria="Complete web development bootcamp",
        issuer_id=dummy_issuer_id,
        tags=["web", "development", "fullstack"],
    )
    api.add_badge(
        name="Doc Writer",
        image="doc_writer.png",
        desc="Created comprehensive project documentation",
        criteria="Write 50 pages of documentation",
        issuer_id=dummy_issuer_id,
        tags=["documentation", "writing", "communication"],
    )
    api.add_badge(
        name="OSS Contributor",
        image="oss_contributor.png",
        desc="Active contributor to open source projects and python ecosystems",
        criteria="Contribute to 3 open source projects",
        issuer_id=dummy_issuer_id,
        tags=["opensource", "python", "community"],
    )
    return 5


@pytest.fixture
def tagged_badges(create_badge_with_legacy):
    """Create badges with tags, both legacy and non-legacy."""
    legacy_tagged = create_badge_with_legacy(
        name="Legacy Python Badge",
        legacy=True,
        tags="python, legacy, programming",
    )
    active_tagged = create_badge_with_legacy(
        name="Active Python Badge",
        tags="python, active, programming",
    )

    return legacy_tagged, active_tagged


def test_add_badges(api, dummy_badge_id):
    assert api.get_badge("testbadge").__str__() == "TestBadge"
    assert api.badge_exists("testbadge") is True


def test_add_badge_creates_tag_relationships(api, dummy_issuer_id):
    badge_id = api.add_badge(
        "TaggedBadge",
        "tagged.png",
        "A badge with normalized tags",
        "Tag criteria",
        dummy_issuer_id,
        tags=["python", "testing"],
    )

    badge = api.get_badge(badge_id)

    assert {tag.name for tag in badge.tags} == {"python", "testing"}
    assert len(badge.tags) == 2


def test_add_badge_reuses_existing_tags(api, dummy_issuer_id):
    api.add_badge(
        "FirstTaggedBadge",
        "first.png",
        "First badge with a shared tag",
        "First criteria",
        dummy_issuer_id,
        tags=["shared", "first"],
    )
    api.add_badge(
        "SecondTaggedBadge",
        "second.png",
        "Second badge with a shared tag",
        "Second criteria",
        dummy_issuer_id,
        tags=["shared", "second"],
    )

    assert api.session.query(Tag).filter_by(name="shared").count() == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        # Test individual field updates
        {"name": "UpdatedName"},
        {"image": "UpdatedImage"},
        {"description": "Updated description"},
        {"criteria": "Updated criteria"},
        {"tags": ["updated", "tags"]},
        {"tags": ["updated", "tags"]},
        # Test multiple field updates
        {
            "name": "MultiUpdate",
            "image": "MultiImage",
            "description": "Multi description",
            "criteria": "Multi criteria",
            "tags": ["multi", "tags"],
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
        expected_tags = set(kwargs["tags"])
    else:
        expected_tags = {tag.name for tag in existing_badge.tags}

    # Update
    api.update_badge(dummy_badge_id, **kwargs)

    # Obtain
    updated_badge = api.get_badge(dummy_badge_id)

    # Verify
    assert updated_badge.name == expected_name
    assert updated_badge.image == expected_image
    assert updated_badge.description == expected_description
    assert updated_badge.criteria == expected_criteria
    assert {tag.name for tag in updated_badge.tags} == expected_tags


def test_update_badge_replaces_tags(api, dummy_issuer_id):
    badge_id = api.add_badge(
        "ReplaceTagsBadge",
        "replace.png",
        "A badge whose tags will be replaced",
        "Replace criteria",
        dummy_issuer_id,
        tags=["old", "shared"],
    )

    api.update_badge(badge_id, tags=["new", "shared"])

    updated_badge = api.get_badge(badge_id)
    assert {tag.name for tag in updated_badge.tags} == {"new", "shared"}
    assert api.session.query(Tag).filter_by(name="shared").count() == 1


def test_update_badge_nonexistent(api):
    """Test updating badge which are non-existent and returns False"""
    result = api.update_badge("nonexistent_badge_id", name="UpdatedName")
    assert result is False


def test_update_badge_invalid_fields(api, dummy_badge_id):
    """Test updating badge with invalid fields and raises KeyError"""
    with pytest.raises(KeyError, match="Invalid fields"):
        api.update_badge(dummy_badge_id, invalid_field="value")


@pytest.mark.parametrize("legacy_value", [True, False])
def test_update_badge_legacy_field(api, dummy_badge_id, legacy_value):
    """Test that update_badge can modify the legacy status of a badge"""
    api.update_badge(dummy_badge_id, legacy=legacy_value)
    badge = api.get_badge(dummy_badge_id)
    assert badge.legacy is legacy_value


def test_delete_badge_rejects_legacy_badge(api, dummy_badge_id):
    """Test that delete_badge raises ValueError when the badge is marked as legacy"""
    api.update_badge(dummy_badge_id, legacy=True)

    with pytest.raises(ValueError, match="legacy badge"):
        api.delete_badge(dummy_badge_id)

    assert api.badge_exists(dummy_badge_id) is True


def test_delete_badge_with_tags(api, dummy_issuer_id):
    api.add_badge(
        "DeleteMe",
        "delete.png",
        "A badge to be deleted",
        "Delete criteria",
        dummy_issuer_id,
        tags=["delete-tag", "common-tag"],
    )
    api.add_badge(
        "KeepMe",
        "keep.png",
        "A badge to keep",
        "Keep criteria",
        dummy_issuer_id,
        tags=["common-tag"],
    )

    result = api.delete_badge("deleteme")
    assert result == "deleteme"
    assert api.badge_exists("deleteme") is False
    assert api.badge_exists("keepme") is True

    keep_badge = api.get_badge("keepme")
    assert {tag.name for tag in keep_badge.tags} == {"common-tag"}


def test_badge_legacy_default(api, dummy_badge_id):
    """Test that a newly created badge has legacy=False by default"""
    badge = api.get_badge(dummy_badge_id)
    assert badge.legacy is False


@pytest.mark.parametrize(
    "legacy_value,expected",
    [
        (False, False),
        (True, True),
    ],
)
def test_badge_legacy(api, dummy_badge_id, legacy_value, expected):
    """Test that legacy can be set and retrieved correctly"""
    badge = api.get_badge(dummy_badge_id)
    badge.legacy = legacy_value
    api.session.flush()

    updated_badge = api.get_badge(dummy_badge_id)
    assert updated_badge.legacy is expected


@pytest.mark.parametrize(
    "legacy_value,expected",
    [
        (False, False),
        (True, True),
    ],
)
def test_badge_legacy_in_as_dict(api, dummy_badge_id, legacy_value, expected):
    """Test that as_dict includes the legacy field correctly"""
    badge = api.get_badge(dummy_badge_id)
    badge.legacy = legacy_value
    api.session.flush()

    badge_dict = api.get_badge(dummy_badge_id).as_dict()
    assert "legacy" in badge_dict
    assert badge_dict["legacy"] is expected


def test_badge_as_dict_includes_tag_names(api, dummy_issuer_id):
    badge_id = api.add_badge(
        "DictTagsBadge",
        "dict-tags.png",
        "A badge whose dict includes tag names",
        "Dict criteria",
        dummy_issuer_id,
        tags=["dict", "tags"],
    )

    badge_dict = api.get_badge(badge_id).as_dict()

    assert badge_dict["tags"] == ["dict", "tags"]


def test_get_badges_from_tags(api, dummy_issuer_id):
    # Badge tagged with "test"
    api.add_badge(
        "TestBadgeA",
        "TestImage",
        "A test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags=["test"],
    )

    # Badge tagged with "tester"
    api.add_badge(
        "TestBadgeB",
        "TestImage",
        "A second test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags=["tester"],
    )

    # Badge tagged with both "test" and "tester"
    api.add_badge(
        "TestBadgeC",
        "TestImage",
        "A third test badge for doing unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags=["test", "tester"],
    )

    tags = ["test", "tester"]
    badges_any = api.get_badges_from_tags(tags, match_all=False)
    assert len(badges_any) == 3
    badges_all = api.get_badges_from_tags(tags, match_all=True)
    assert len(badges_all) == 1


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_all_badges_legacy_filtering(api, create_badge_with_legacy, include_legacy):
    """Test that get_all_badges respects include_legacy parameter"""
    legacy_badge = create_badge_with_legacy("Legacy Badge", legacy=True)
    active_badge = create_badge_with_legacy("Active Badge")

    results = list(api.get_all_badges(include_legacy=include_legacy))
    badge_ids = [b.id for b in results]

    assert (legacy_badge in badge_ids) is include_legacy
    assert active_badge in badge_ids


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_badges_from_tags_legacy_filtering(api, tagged_badges, include_legacy):
    """Test that get_badges_from_tags respects include_legacy parameter"""
    legacy_id, active_id = tagged_badges

    results = api.get_badges_from_tags(["python"], include_legacy=include_legacy)
    badge_ids = [b.id for b in results]

    assert (legacy_id in badge_ids) is include_legacy
    assert active_id in badge_ids


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_badges_from_tags_match_all_legacy_filtering(
    api, create_badge_with_legacy, include_legacy
):
    """Test that get_badges_from_tags with match_all=True respects include_legacy"""
    legacy_multi = create_badge_with_legacy(
        name="Legacy Multi Tag",
        legacy=True,
        tags="python, web, legacy",
    )
    active_multi = create_badge_with_legacy(
        name="Active Multi Tag",
        tags="python, web, active",
    )

    results = api.get_badges_from_tags(
        ["python", "web"], match_all=True, include_legacy=include_legacy
    )
    badge_ids = [b.id for b in results]

    assert (legacy_multi in badge_ids) is include_legacy
    assert active_multi in badge_ids


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_badges_by_string_legacy_filtering(api, create_badge_with_legacy, include_legacy):
    """Test that get_badges_by_string respects include_legacy parameter"""
    legacy_search = create_badge_with_legacy(
        "Legacy SearchBadge",
        legacy=True,
    )
    active_search = create_badge_with_legacy("Active SearchBadge")

    results = api.get_badges_by_string("SearchBadge", include_legacy=include_legacy)
    badge_ids = [b.id for b in results["badges"]]

    assert (legacy_search in badge_ids) is include_legacy
    assert active_search in badge_ids


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_badges_by_string_description_search_legacy_filtering(
    api, create_badge_with_legacy, include_legacy
):
    """Test that get_badges_by_string searches descriptions and respects include_legacy"""
    legacy_desc = create_badge_with_legacy(
        name="Badge One",
        legacy=True,
        desc="This is a legacy special description",
    )
    active_desc = create_badge_with_legacy(
        name="Badge Two",
        desc="This is an active special description",
    )

    results = api.get_badges_by_string("special description", include_legacy=include_legacy)
    badge_ids = [b.id for b in results["badges"]]

    assert (legacy_desc in badge_ids) is include_legacy
    assert active_desc in badge_ids


@pytest.mark.parametrize(
    "query, expected_total, must_contain",
    [
        ("Python Expert", 1, ["Python Expert"]),
        ("python", 2, ["Python Expert", "OSS Contributor"]),
        ("PYTHON", 2, ["Python Expert", "OSS Contributor"]),
        ("web developer", 1, ["Frontend Master"]),
        ("documentation", 1, ["Doc Writer"]),
        ("nonexistent_badge_xyz", 0, []),
        (
            "",
            5,
            [
                "Python Expert",
                "OSS Contributor",
                "Frontend Master",
                "Doc Writer",
                "JavaScript Ninja",
            ],
        ),
    ],
)
def test_search_filter_conditions(query, expected_total, must_contain, api, search_test_badges):
    result = api.get_badges_by_string(query)

    assert result["total"] == expected_total
    badge_names = [b.name for b in result["badges"]]
    for name in must_contain:
        assert name in badge_names


@pytest.mark.parametrize(
    "query, begin, limit, expected_begin, expected_limit, expected_count",
    [
        ("python", 0, 100, 0, 100, 2),
        ("python", 0, 1, 0, 1, 1),
        ("python", 1, 1, 1, 1, 1),
        ("python", 500, 1, 500, 1, 0),
        ("", 0, 500, 0, 100, 5),
    ],
)
def test_search_pagination_conditions(
    query,
    begin,
    limit,
    expected_begin,
    expected_limit,
    expected_count,
    api,
    search_test_badges,
):
    result = api.get_badges_by_string(query, begin=begin, limit=limit)

    assert result["limit"] == expected_limit
    assert len(result["badges"]) == expected_count
    assert result["total"] >= expected_count


def test_cleanup_orphan_tags(api, dummy_issuer_id):
    api.add_badge(
        "OrphanBadge",
        "orphan.png",
        "A badge whose tags may become orphans",
        "Orphan criteria",
        dummy_issuer_id,
        tags=["unique-tag", "shared-tag"],
    )
    api.add_badge(
        "KeeperBadge",
        "keeper.png",
        "A badge that keeps shared-tag alive",
        "Keeper criteria",
        dummy_issuer_id,
        tags=["shared-tag", "keeper-tag"],
    )

    assert api.session.query(Tag).count() == 3

    api.delete_badge("orphanbadge")
    deleted = api.cleanup_orphan_tags()

    assert deleted == 1
    remaining = {t.name for t in api.session.query(Tag).all()}
    assert "unique-tag" not in remaining
    assert "shared-tag" in remaining
    assert "keeper-tag" in remaining
