import datetime

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Mapper

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


def test_badge_cascade_delete(api):
    """Verify that deleting a badge automatically cascades and deletes related records."""

    # 1. Setup Data
    issuer_id = api.add_issuer("test origin", "test issuer", "test org", "test contact")

    # add_badge returns the created Badge ID
    badge_id = api.add_badge(
        "test cascade badge",
        "test.png",
        "desc",
        "crit",
        issuer_id,
        tags=["cascade"],
    )
    badge = api.session.get(model.Badge, badge_id)

    # add_person might return an ID or an object, wait let's just fetch it
    person_email = "test@cascade.com"
    api.add_person(person_email)

    # Add child records
    api.add_assertion(badge.id, person_email, datetime.datetime.now())
    api.add_authorization(badge.id, person_email)
    api.add_invitation(badge.id, created_by_email=person_email)
    api.set_current_value(badge.id, person_email, 1)

    team_id = api.create_team("Cascade Team")
    series_id = api.create_series("Cascade Series", "A series for cascade tests", team_id)
    api.create_milestone(1, badge.id, series_id)

    # Verify everything was created
    assert api.session.query(model.Badge).count() == 1
    assert api.session.query(model.Assertion).count() == 1
    assert api.session.query(model.Authorization).count() == 1
    assert api.session.query(model.Invitation).count() == 1
    assert api.session.query(model.CurrentValue).count() == 1
    assert api.session.query(model.Milestone).count() == 1
    assert api.session.execute(text("select count(*) from badge_tags")).scalar_one() == 1

    # 2. Delete the badge
    # Because of passive_deletes=True, SQLAlchemy will NOT fetch the assertions
    # to delete them manually. It will just delete the badge and let the database do it.
    api.session.delete(badge)
    api.session.commit()

    # 3. Verify Cascade
    # The badge should be gone, and the database should have cascaded the delete
    # to the child records.
    assert api.session.query(model.Badge).count() == 0
    assert api.session.query(model.Assertion).count() == 0
    assert api.session.query(model.Authorization).count() == 0
    assert api.session.query(model.Invitation).count() == 0
    assert api.session.query(model.CurrentValue).count() == 0
    assert api.session.query(model.Milestone).count() == 0
    assert api.session.execute(text("select count(*) from badge_tags")).scalar_one() == 0
