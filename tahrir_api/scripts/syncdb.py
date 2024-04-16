import os
import sys

from .utils import get_db_manager_from_paste


def usage(argv):
    cmd = os.path.basename(argv[0])
    print(f"usage: {cmd} <config_uri>\n '(example: \"{cmd} development.ini\"'")
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    db_mgr = get_db_manager_from_paste(config_uri)
    db_mgr.sync()
