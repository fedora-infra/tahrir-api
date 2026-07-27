import click

from ..dbapi import TahrirDatabase
from .utils import get_db_manager_from_config


@click.command()
@click.argument("config", type=click.Path(exists=True))
def main(config: str) -> None:
    db_mgr = get_db_manager_from_config(config)
    with db_mgr.Session() as session:
        db = TahrirDatabase(session=session)
        db.compute_badge_rarities()
