
import datetime
import os
import random
import sys
import transaction

from sqlalchemy import engine_from_config
from paste.deploy import appconfig

from ..model import (
    DBSession,
    Issuer,
    Badge,
    Person,
    Team,
    Milestone,
    Series,
    Assertion,
    DeclarativeBase,
)
from ..utils import convert_name_to_id


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def _getpathsec(config_uri, name):
    if '#' in config_uri:
        path, section = config_uri.split('#', 1)
    else:
        path, section = config_uri, 'main'
    if name:
        section = name
    return path, section


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    path, section = _getpathsec(config_uri, "pyramid")
    config_name = 'config:%s' % path
    here_dir = os.getcwd()

    global_conf = None
    if 'OPENSHIFT_APP_NAME' in os.environ:
        if 'OPENSHIFT_MYSQL_DB_URL' in os.environ:
            template = '{OPENSHIFT_MYSQL_DB_URL}{OPENSHIFT_APP_NAME}'
        elif 'OPENSHIFT_POSTGRESQL_DB_URL' in os.environ:
            template = '{OPENSHIFT_POSTGRESQL_DB_URL}{OPENSHIFT_APP_NAME}'

        global_conf = {
            'sqlalchemy.url': template.format(**os.environ)
        }

    settings = appconfig(config_name, name=section, relative_to=here_dir,
                         global_conf=global_conf)

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    DeclarativeBase.metadata.create_all(engine)

    with transaction.manager:
        issuer = Issuer(
            name="Fedoraproject",
            origin="http://badges.fedoraproject.org",
            org="fedoraproject.org",
            contact="badges@fedoraproject.org",
        )
        DBSession.add(issuer)

        BADGES_PNGS_URL = 'https://badges.fedoraproject.org/pngs/{badge_png}'
        FEDORAHOSTED_URL = 'https://fedorahosted.org/fedora-badges/ticket/212'

        COPR_SERIES = [
            'copr-build.png',
            'copr-build-20.png',
            'copr-build-90.png',
            'copr-build-150.png',
            'copr-build-300.png',
            'copr-build-999.png',
        ]

        FAS_ACCOUNT_SERIES = [
            'fas-account-embryo.png',
            'fas-account-egg.png',
            'fas-account-tadpole.png',
            'fas-account-tadpole-with-legs.png',
            'fas-account-froglet.png',
            'fas-account-adult-frog.png',
        ]

        BADGE_ARTIST_SERIES = [
            'badge-artist-1.png',
            'badge-artist-2.png',
            'badge-artist-3.png',
            'badge-artist-4.png',
            'badge-artist-5.png',
        ]

        TESTER_SERIES = [
            'tester-01.png',
            'tester-02.png',
            'tester-03.png',
            'tester-04.png',
            'tester-05.png',
            'tester-06.png',
            'tester-07.png',
            'tester-08.png',
            'tester-09.png',
            'tester-10.png',
        ]

        USERS = ['sayanchowdhury', 'ralph', 'maxamillion', 'duffy']

        SERIES = {
            'copr-series': COPR_SERIES,
            'fas-account-series': FAS_ACCOUNT_SERIES,
            'badge-artist-series': BADGE_ARTIST_SERIES,
            'tester-series': TESTER_SERIES,
        }

        TEAMS_SERIES_MAP = {
            'infrastructure': ['copr-series', 'fas-account-series'],
            'qa': ['tester-series'],
            'design': ['badge-artist-series'],
        }

        SERIES_TAG_MAP = {
            'copr-series': 'development, copr',
            'fas-account-series': 'lifecycle, community',
            'badge-artist-series': 'content, design, badges',
            'tester-series': 'development, qa',
        }

        for name, series in TEAMS_SERIES_MAP.iteritems():
            team = Team(
                name=name,
            )
            DBSession.add(team)

        for name, series in TEAMS_SERIES_MAP.iteritems():
            for elem in series:
                name = desc = ' '.join(elem.split('-')).title()
                series = Series(
                    name=name,
                    description=desc,
                    team_id=name,
                    tags=SERIES_TAG_MAP.get(elem, '')
                )

        badge_series = {}
        for slug, serie in SERIES.iteritems():
            badge_series[slug] = []
            for position, elem in enumerate(serie, 1):
                name = ' '.join(elem.split('.png')[0].split('-')).title()
                image = BADGES_PNGS_URL.format(badge_png=elem)
                criteria = FEDORAHOSTED_URL.format(random.randint(1, 999))

                badge = Badge(
                    id=convert_name_to_id(name),
                    name=name,
                    image=image,
                    description=name,
                    criteria=criteria,  # TODO -- how should this work?
                    issuer=issuer,
                    tags=SERIES_TAG_MAP.get(slug, '')
                )
                DBSession.add(badge)
                badge_series[slug].append(badge)
                
                milestone = Milestone(
                    position=position,
                    badge_id=badge.id,
                    series_id=slug
                )
                DBSession.add(milestone)

        persons = []
        for user in USERS:
            person = Person(
                email='{username}@fedoraproject.org'.format(username=user),
            )
            DBSession.add(person)
            persons.append(person)

        def award_badges(person):
            """ Award badge to user in any series """
            for slug, series in badge_series.iteritems():
                num_series = len(series)
                series = series[:random.randint(0, num_series)]
                for badge in series:
                    assertion = Assertion(
                        badge_id=badge.id,
                        person=person,
                        issued_on=datetime.datetime.now(),
                    )
                    DBSession.add(assertion)

        for person in persons:
            award_badges(person)
