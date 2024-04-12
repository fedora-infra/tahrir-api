import datetime
import os
import pprint
import sys

import transaction
from paste.deploy import appconfig
from sqlalchemy import engine_from_config

from ..model import Assertion, Badge, DBSession, DeclarativeBase, Issuer, Person


def usage(argv):
    cmd = os.path.basename(argv[0])
    print(f"usage: {cmd} <config_uri>\n '(example: \"{cmd} development.ini\"'")
    sys.exit(1)


def _getpathsec(config_uri, name):
    if "#" in config_uri:
        path, section = config_uri.split("#", 1)
    else:
        path, section = config_uri, "main"
    if name:
        section = name
    return path, section


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    path, section = _getpathsec(config_uri, "pyramid")
    config_name = "config:%s" % path
    here_dir = os.getcwd()

    global_conf = None
    if "OPENSHIFT_APP_NAME" in os.environ:
        if "OPENSHIFT_MYSQL_DB_URL" in os.environ:
            template = "{OPENSHIFT_MYSQL_DB_URL}{OPENSHIFT_APP_NAME}"
        elif "OPENSHIFT_POSTGRESQL_DB_URL" in os.environ:
            template = "{OPENSHIFT_POSTGRESQL_DB_URL}{OPENSHIFT_APP_NAME}"

        global_conf = {"sqlalchemy.url": template.format(**os.environ)}

    settings = appconfig(config_name, name=section, relative_to=here_dir, global_conf=global_conf)

    engine = engine_from_config(settings, "sqlalchemy.")
    DBSession.configure(bind=engine)
    DeclarativeBase.metadata.create_all(engine)
