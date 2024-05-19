import click
from fasjson_client import Client as FasjsonClient
from fasjson_client.errors import APIError
from sqlalchemy import func, select

from ..model import Person
from .utils import get_db_manager_from_paste


@click.command()
@click.argument("paste-config", type=click.Path(exists=True))
@click.argument("fasjson-url", required=True)
def main(paste_config, fasjson_url):
    fasjson = FasjsonClient(url=fasjson_url)

    db_mgr = get_db_manager_from_paste(paste_config)
    with db_mgr.Session() as session:
        query = select(Person).where(
            Person.email.like("%@fedoraproject.org"),
            Person._avatar.is_(None),
            Person.opt_out.is_(False),
        )
        total = session.scalar(query.with_only_columns(func.count(Person.id)))
        click.echo(f"Found {total} users to update.")
        with click.progressbar(
            session.scalars(query),
            length=total,
            label="Setting avatar",
            item_show_func=lambda p: p.nickname if p else "",
        ) as persons:
            for person in persons:
                try:
                    fas_user = fasjson.get_user(username=person.nickname).result
                except APIError as e:
                    if e.code == 404:
                        click.echo(
                            f"User {person.nickname} ({person.email}) not found in FASJSON, "
                            "skipping"
                        )
                        continue
                    else:
                        raise
                person._avatar = fas_user["emails"][0]
                # print(f"Setting {person.nickname}'s avatar to {person._avatar}")
                session.commit()
