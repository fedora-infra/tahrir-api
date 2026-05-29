import pytest

from tahrir_api.model import Badge, Milestone, Series, Tag, Team


@pytest.fixture
def team_with_legacy_badges(api, create_badge_with_legacy):
    """Create a team with both legacy and non-legacy badges."""
    team_id = api.create_team("TestTeam")
    series_id = api.create_series("TestSeries", "A test series", team_id, "test, series")

    legacy_badge = create_badge_with_legacy("Legacy Team Badge", legacy=True)
    active_badge = create_badge_with_legacy("Active Team Badge")

    api.create_milestone(1, legacy_badge, series_id)
    api.create_milestone(2, active_badge, series_id)

    return team_id, legacy_badge, active_badge


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


def test_create_series_creates_tag_relationships(api):
    team_id = api.create_team("SeriesTeam")

    series_id = api.create_series(
        "TaggedSeries",
        "A series with normalized tags",
        team_id,
        tags="python, testing",
    )

    series = api.get_series(series_id)

    assert {tag.name for tag in series.tags} == {"python", "testing"}
    assert len(series.tags) == 2


def test_create_series_deduplicates_comma_separated_tags(api):
    team_id = api.create_team("DedupSeriesTeam")

    series_id = api.create_series(
        "DedupTaggedSeries",
        "A series with duplicate tags",
        team_id,
        tags="python, testing, python,  testing  ,",
    )

    series = api.get_series(series_id)

    assert {tag.name for tag in series.tags} == {"python", "testing"}
    assert api.session.query(Tag).filter_by(name="python").count() == 1


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
    )
    series_b = Series(
        id="test-series-bravo",
        name="Test Series Bravo",
        description="Bravo test series",
        team_id="test-team",
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
        team_id="test-team",
    )
    api.session.add(series)
    api.session.flush()

    retrieved_series = api.get_series("test-series")
    assert retrieved_series is not None
    assert retrieved_series.id == "test-series"
    assert retrieved_series.name == "Test Series"
    assert retrieved_series.description == "A test series for unit testing"
    assert retrieved_series.tags == []


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


def test_series_as_dict_includes_tag_names(api):
    team_id = api.create_team("DictSeriesTeam")
    series_id = api.create_series(
        "DictTagsSeries",
        "A series whose dict includes tag names",
        team_id,
        tags="dict, tags",
    )

    series_dict = api.get_series(series_id).as_dict()

    assert series_dict["tags"] == ["dict", "tags"]


@pytest.mark.parametrize("include_legacy", [False, True])
def test_get_badges_from_team_legacy_filtering(api, team_with_legacy_badges, include_legacy):
    """Test that get_badges_from_team respects include_legacy parameter"""
    team_id, legacy_badge, active_badge = team_with_legacy_badges

    results = api.get_badges_from_team(team_id, include_legacy=include_legacy)
    badge_ids = [b.id for b in results]

    assert (legacy_badge in badge_ids) is include_legacy
    assert active_badge in badge_ids
