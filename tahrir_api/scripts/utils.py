import types

from ..utils import get_db_manager_from_uri


def _get_config_from_path(filename):
    # See flask.config.Config.from_pyfile()
    d = types.ModuleType("config")
    d.__file__ = filename
    try:
        with open(filename, mode="rb") as config_file:
            exec(compile(config_file.read(), filename, "exec"), d.__dict__)  # noqa: S102
    except OSError as e:
        e.strerror = f"Unable to load configuration file ({e.strerror})"
        raise
    config = {}
    for key in dir(d):
        if key.isupper():
            config[key] = getattr(d, key)
    return config


def get_db_manager_from_config(filename):
    config = _get_config_from_path(filename)
    dburi = config["SQLALCHEMY_DATABASE_URI"]
    return get_db_manager_from_uri(dburi)
