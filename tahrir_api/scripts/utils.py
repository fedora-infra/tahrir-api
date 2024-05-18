import importlib.resources
import os

from paste.deploy import appconfig
from sqlalchemy_helpers import DatabaseManager

from ..model import Assertion, Badge, DeclarativeBase, Issuer, Person  # noqa: F401


def _getpathsec(config_uri, name):
    if "#" in config_uri:
        path, section = config_uri.split("#", 1)
    else:
        path, section = config_uri, "main"
    if name:
        section = name
    return path, section


def get_db_manager_from_paste(config_uri):
    path, section = _getpathsec(config_uri, "pyramid")
    config_name = f"config:{path}"
    here_dir = os.getcwd()

    global_conf = None
    if "OPENSHIFT_APP_NAME" in os.environ:
        if "OPENSHIFT_MYSQL_DB_URL" in os.environ:
            template = "{OPENSHIFT_MYSQL_DB_URL}{OPENSHIFT_APP_NAME}"
        elif "OPENSHIFT_POSTGRESQL_DB_URL" in os.environ:
            template = "{OPENSHIFT_POSTGRESQL_DB_URL}{OPENSHIFT_APP_NAME}"

        global_conf = {"sqlalchemy.url": template.format(**os.environ)}

    settings = appconfig(config_name, name=section, relative_to=here_dir, global_conf=global_conf)

    prefix = "sqlalchemy."
    db_options = {key[len(prefix) :]: settings[key] for key in settings if key.startswith(prefix)}
    dburi = db_options.pop("url")
    with importlib.resources.as_file(
        importlib.resources.files("tahrir_api").joinpath("migrations")
    ) as alembic_path:
        return DatabaseManager(dburi, alembic_path.as_posix())
