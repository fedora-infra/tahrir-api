from argparse import ArgumentParser

from fasjson_client import Client as FasjsonClient
from sqlalchemy import select

from ..model import Person
from .utils import get_db_manager_from_paste


def main():
    args_parser = ArgumentParser()
    args_parser.add_argument("config", help="Paste configuration file (ini)")
    args_parser.add_argument("fasjson", help="The URL to FASJSON")
    args = args_parser.parse_args()

    fasjson = FasjsonClient(url=args.fasjson)

    db_mgr = get_db_manager_from_paste(args.config)
    with db_mgr.Session() as session:
        for person in session.scalars(select(Person)):
            fas_user = fasjson.get_user(username=person.nickname).result
            person._avatar = fas_user["emails"][0]
            print(f"Setting {person.nickname}'s avatar to {person._avatar}")
        session.commit()
