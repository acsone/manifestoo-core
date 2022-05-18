from manifestoo_core.core_addons import (
    get_core_addon_license,
    is_core_addon,
    is_core_ce_addon,
    is_core_ee_addon,
)
from manifestoo_core.odoo_series import OdooSeries


def test_is_core_ce_addon():
    assert is_core_ce_addon("base", OdooSeries.v8_0)
    assert is_core_ce_addon("base", OdooSeries.v8_0)
    assert is_core_ce_addon("account", OdooSeries.v14_0)
    assert not is_core_ce_addon("account_accountant", OdooSeries.v14_0)


def test_is_core_ee_addon():
    assert not is_core_ee_addon("base", OdooSeries.v8_0)
    assert not is_core_ee_addon("base", OdooSeries.v8_0)
    assert not is_core_ee_addon("account", OdooSeries.v14_0)
    assert is_core_ee_addon("account_accountant", OdooSeries.v14_0)


def test_is_core_addon():
    assert is_core_addon("base", OdooSeries.v8_0)
    assert is_core_addon("base", OdooSeries.v8_0)
    assert is_core_addon("account", OdooSeries.v14_0)
    assert is_core_addon("account_accountant", OdooSeries.v14_0)


def test_get_core_addon_license():
    assert get_core_addon_license("base", OdooSeries.v8_0) == "AGPL-3"
    assert get_core_addon_license("base", OdooSeries.v9_0) == "LGPL-3"
    assert get_core_addon_license("account_accountant", OdooSeries.v14_0) == "OEEL-1"
