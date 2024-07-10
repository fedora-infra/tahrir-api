import os
import sys

import click

from .utils import get_db_manager_from_config


def usage(argv):
    cmd = os.path.basename(argv[0])
    print(f"usage: {cmd} <config_uri>\n '(example: \"{cmd} development.ini\"'")
    sys.exit(1)


@click.command()
@click.argument("config", type=click.Path(exists=True))
def main(config):
    db_mgr = get_db_manager_from_config(config)
    db_mgr.sync()
