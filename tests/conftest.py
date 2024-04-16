import pytest

from tahrir_api.dbapi import TahrirDatabase


@pytest.fixture
def callback_calls():
    return []


@pytest.fixture
def api(callback_calls, tmp_path):
    def callback(*args, **kwargs):
        callback_calls.append((args, kwargs))

    dbapi = TahrirDatabase(
        f"sqlite:///{tmp_path.as_posix()}/testdb.db", notification_callback=callback
    )
    dbapi.db_mgr.sync()
    return dbapi
