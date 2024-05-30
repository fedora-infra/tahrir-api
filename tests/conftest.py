import pytest

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
    db_api = TahrirDatabase(db_uri, notification_callback=callback)
    db_mgr = get_db_manager_from_uri(db_uri)
    db_mgr.sync()
    return db_api
