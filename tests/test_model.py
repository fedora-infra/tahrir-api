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
