from pathlib import Path
from typing import Optional, Tuple

from .exceptions import (
    AddonNotFound,
    AddonNotFoundInvalidManifest,
    AddonNotFoundNoInit,
    AddonNotFoundNoManifest,
    AddonNotFoundNotADirectory,
    AddonNotFoundNotInstallable,
)
from .manifest import InvalidManifest, Manifest, get_manifest_path
from .odoo_series import OdooSeries, detect_from_addon_version

__all__ = [
    "Addon",
    "is_addon_dir",
]


def is_addon_dir(addon_dir: Path, allow_not_installable: bool = False) -> bool:
    """Detect if a directory contains an Odoo addon.

    :param addon_dir: The directory to check.
    :param allow_not_installable: Whether to allow the addon to be have
        installable=False in its manifest.
    """
    try:
        Addon.from_addon_dir(addon_dir, allow_not_installable)
    except AddonNotFound:
        return False
    else:
        return True


class Addon:
    """Represent a concrete addon manifest."""

    manifest: Manifest
    "The addon's manifest."
    manifest_path: Path
    "The path to the addon's manifest file."
    name: str
    "The addon's name."

    def __init__(
        self,
        manifest: Manifest,
        manifest_path: Path,
        name: Optional[str] = None,
    ) -> None:
        """Do not use this constructor, use the from_addon_dir classmethod instead."""
        self.manifest = manifest
        self.manifest_path = manifest_path
        self.path = self.manifest_path.parent
        if name is None:
            self.name = self.path.name
        else:
            self.name = name

    @classmethod
    def from_addon_dir(
        cls,
        addon_dir: Path,
        allow_not_installable: bool = False,
    ) -> "Addon":
        """Obtain an Addon object from an addon directory path.

        Raises an :class:`AddonNotFound` exception if the directory is not a valid addon
        directory, or if ``allow_not_installable`` is False and the addon is not
        installable.
        """
        if not addon_dir.is_dir():
            msg = f"{addon_dir} is not a directory"
            raise AddonNotFoundNotADirectory(msg)
        manifest_path = get_manifest_path(addon_dir)
        if not manifest_path:
            msg = f"No manifest file found in {addon_dir}"
            raise AddonNotFoundNoManifest(msg)
        try:
            manifest = Manifest.from_file(manifest_path)
            if not allow_not_installable and not manifest.installable:
                msg = f"{addon_dir} is not installable"
                raise AddonNotFoundNotInstallable(msg)
        except InvalidManifest as e:
            raise AddonNotFoundInvalidManifest(str(e)) from e
        if not addon_dir.joinpath("__init__.py").is_file() and _requires_init(manifest):
            msg = f"{addon_dir} is missing an __init__.py"
            raise AddonNotFoundNoInit(msg)
        return cls(manifest, manifest_path)


def _requires_init(manifest: Manifest) -> bool:
    """Whether an addon needs an ``__init__.py`` to be loaded by Odoo.

    Since Odoo 13.0, addons are imported with ``importlib``, so an addon
    without ``__init__.py`` (a data-only addon) is a valid namespace package.
    Up to Odoo 12.0, the addon had to be a regular package. The Odoo series
    is detected from the addon version, when it is recognized.
    """
    if not manifest.version:
        return False
    odoo_series = detect_from_addon_version(manifest.version)
    if odoo_series is None:
        return False
    return _series_tuple(odoo_series) < _series_tuple(OdooSeries.v13_0)


def _series_tuple(odoo_series: str) -> Tuple[int, ...]:
    return tuple(int(part) for part in odoo_series.split("."))
