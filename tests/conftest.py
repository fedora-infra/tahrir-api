import pytest
from sqlalchemy_helpers import Base as DeclarativeBase

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.utils import get_db_manager_from_uri


@pytest.fixture
def callback_calls():
    return []


@pytest.fixture
def api(callback_calls, tmp_path):
    def callback(*args, **kwargs):
        callback_calls.append((args, kwargs))

    db_uri = f"sqlite:///{tmp_path.as_posix()}/testdb.db"
    db_mgr = get_db_manager_from_uri(db_uri)
    # Use create_all directly to avoid Alembic multi-head issues in tests.
    # Tests always start with a fresh DB so migration history is not needed.
    DeclarativeBase.metadata.create_all(bind=db_mgr.engine)
    db_api = TahrirDatabase(db_uri, notification_callback=callback)

    yield db_api

    db_api.session.close()
    db_mgr.engine.dispose()


# ---------------------------------------------------------------------------
# Cross-domain fixtures
# Used by ≥2 test modules; single-file fixtures stay local to their module.
# ---------------------------------------------------------------------------


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
def create_badge_with_legacy(api, dummy_issuer_id):
    """Factory fixture for creating badges with optional legacy status.

    Consumed by test_badges.py (legacy-filtering tests) and
    test_teams_series.py (via team_with_legacy_badges), so it lives here
    rather than in any single file.
    """

    def _create_badge(name, legacy=False, desc=None, tags=None):
        badge_id = api.add_badge(
            name=name,
            image=f"{name.lower().replace(' ', '_')}.png",
            desc=desc or f"{name} description",
            criteria=f"{name} criteria",
            issuer_id=dummy_issuer_id,
            tags=tags,
        )
        badge = api.get_badge(badge_id)
        badge.legacy = legacy
        api.session.flush()
        return badge_id

    return _create_badge
