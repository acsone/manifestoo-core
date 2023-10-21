import pytest

from manifestoo_core.exceptions import UnsupportedOdooSeries
from manifestoo_core.odoo_series import (
    OdooSeries,
    detect_from_addon_version,
    detect_from_addons_set,
)

from .common import mock_addons_set


def test_detect_from_version() -> None:
    assert detect_from_addon_version("1.0.0") is None
    assert detect_from_addon_version("1.0.0.0.0.0") is None
    assert detect_from_addon_version("8.0.1") is None
    assert detect_from_addon_version("8.0.1.0") is None
    assert detect_from_addon_version("8.0.1.0.0") == OdooSeries.v8_0
    assert detect_from_addon_version("14.0.1.0.0.1") == OdooSeries.v14_0


def test_detect_none() -> None:
    addons_set = mock_addons_set(
        {
            "a": {"version": "1.0.0"},
            "b": {},
        },
    )
    assert detect_from_addons_set(addons_set) == set()


def test_detect_one() -> None:
    addons_set = mock_addons_set(
        {
            "a": {"version": "1.0.0"},
            "b": {"version": "12.0.1.0.0"},
        },
    )
    assert detect_from_addons_set(addons_set) == {OdooSeries.v12_0}


def test_detect_ambiguous() -> None:
    addons_set = mock_addons_set(
        {
            "a": {"version": "13.0.1.0.0"},
            "b": {"version": "12.0.1.0.0"},
        },
    )
    assert detect_from_addons_set(addons_set) == {OdooSeries.v12_0, OdooSeries.v13_0}


def test_series_from_str() -> None:
    assert OdooSeries.from_str("10.0") == OdooSeries.v10_0


def test_unsupported_series_from_str() -> None:
    with pytest.raises(UnsupportedOdooSeries):
        OdooSeries.from_str("7.0")
