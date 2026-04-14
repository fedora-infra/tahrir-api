import pytest
from sqlalchemy import inspect
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


def test_badge_assertion_cascade_delete(api):
    """
    Verify that deleting a badge automatically removes associated assertions.
    """
    session = api.session
    issuer_id = api.add_issuer("TestOrigin", "TestIssuer", "TestOrg", "TestContact")
    api.add_person("cascade@example.com")
    badge_id = api.add_badge(
        "CascadeBadge", "TestImage", "Testing delete", "TestCriteria", issuer_id
    )
    api.add_assertion(badge_id, "cascade@example.com", None)
    session.commit()

    assert session.query(model.Assertion).filter_by(badge_id=badge_id).count() == 1

    badge = api.get_badge(badge_id)
    session.delete(badge)
    session.commit()

    assert session.query(model.Assertion).filter_by(badge_id=badge_id).count() == 0
