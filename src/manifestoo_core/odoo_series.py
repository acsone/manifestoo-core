"""Odoo Series and Editions."""
from enum import Enum
from typing import Optional, Set

from .addons_set import AddonsSet

__all__ = [
    "OdooSeries",
    "OdooEdition",
    "detect_from_addon_version",
    "detect_from_addons_set",
]


class OdooSeries(str, Enum):
    """Enum representing an Odoo Series (also known as Version)."""

    v8_0 = "8.0"
    v9_0 = "9.0"
    v10_0 = "10.0"
    v11_0 = "11.0"
    v12_0 = "12.0"
    v13_0 = "13.0"
    v14_0 = "14.0"
    v15_0 = "15.0"
    v16_0 = "16.0"


class OdooEdition(str, Enum):
    """Enum representing an Odoo Edition."""

    CE = "c"
    EE = "e"


def detect_from_addon_version(version: str) -> Optional[OdooSeries]:
    """Detect the Odoo Series from an addon version.

    Returns ``None`` if the version is not recognized.
    """
    parts = version.split(".")
    if len(parts) < 5:
        return None
    try:
        return OdooSeries(".".join(parts[:2]))
    except ValueError:
        return None


def detect_from_addons_set(addons_set: AddonsSet) -> Set[OdooSeries]:
    detected: Set[OdooSeries] = set()
    for addon in addons_set.values():
        addon_version = addon.manifest.version
        if not addon_version:
            continue
        addon_series = detect_from_addon_version(addon_version)
        if not addon_series:
            continue
        detected.add(addon_series)
    return detected
