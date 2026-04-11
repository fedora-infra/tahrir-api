import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Mapper, sessionmaker

from tahrir_api import model


def get_models_columns_with_defaults():
    models_columns_as_params = []

    for name, thing in model.__dict__.items():
        if isinstance(thing, type):
            try:
                inspected = inspect(thing)
            except NoInspectionAvailable:
                continue

            if isinstance(inspected, Mapper):
                for colname, column in inspected.c.items():
                    default = getattr(column, "default", None)
                    if default is None:
                        continue
                    if hasattr(default, "arg"):
                        models_columns_as_params.append(
                            pytest.param(column, id=f"{name}.{colname}")
                        )

    return models_columns_as_params


@pytest.mark.parametrize("column", get_models_columns_with_defaults())
def test_safe_column_default(column):
    if getattr(column.default, "is_callable", False):
        column.default.arg(None)

def test_tag_normalization_relationships():
    engine = create_engine("sqlite:///:memory:")
    model.DeclarativeBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create Tags
    tag_dev = model.Tag(name="developer")
    tag_web = model.Tag(name="web")
    session.add_all([tag_dev, tag_web])
    
    # Create Issuer and Team 
    issuer = model.Issuer(origin="org", name="Org", org="Org", contact="c@o.com")
    team = model.Team(id="team-1", name="Team One")
    session.add_all([issuer, team])
    session.flush()

    # Create Badge and Series
    badge = model.Badge(
        id="b1", name="B1", image="i.png", description="D", 
        criteria="C", issuer_id=issuer.id
    )
    series = model.Series(
        id="s1", name="S1", description="D", team_id=team.id
    )

    # Associate Tags 
    badge.tags.append(tag_dev)
    badge.tags.append(tag_web)
    series.tags.append(tag_dev)
    
    session.add_all([badge, series])
    session.commit()

    # Assertions
    # Test Badge many-to-many
    assert len(badge.tags) == 2
    assert tag_dev in badge.tags
    assert tag_web in badge.tags

    # Test Series many-to-many
    assert len(series.tags) == 1
    assert tag_dev in series.tags

    # Test the backrefs 
    assert badge in tag_dev.badges
    assert series in tag_dev.series
    
    session.close()