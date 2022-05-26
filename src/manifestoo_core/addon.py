from pathlib import Path
from typing import Optional

from .exceptions import (
    AddonNotFoundInvalidManifest,
    AddonNotFoundNoInit,
    AddonNotFoundNoManifest,
    AddonNotFoundNotADirectory,
    AddonNotFoundNotInstallable,
)
from .manifest import InvalidManifest, Manifest, get_manifest_path

__all__ = [
    "Addon",
]


class Addon:
    """Represent a concrete addon manifest."""

    def __init__(
        self, manifest: Manifest, manifest_path: Path, name: Optional[str] = None
    ):
        self.manifest = manifest
        self.manifest_path = manifest_path
        self.path = self.manifest_path.parent
        if name is None:
            self.name = self.path.name
        else:
            self.name = name

    @classmethod
    def from_addon_dir(
        cls, addon_dir: Path, allow_not_installable: bool = False
    ) -> "Addon":
        if not addon_dir.is_dir():
            raise AddonNotFoundNotADirectory(f"{addon_dir} is not a directory")
        manifest_path = get_manifest_path(addon_dir)
        if not manifest_path:
            raise AddonNotFoundNoManifest(f"No manifest file found in {addon_dir}")
        try:
            manifest = Manifest.from_file(manifest_path)
            if not allow_not_installable and not manifest.installable:
                raise AddonNotFoundNotInstallable(f"{addon_dir} is not installable")
        except InvalidManifest as e:
            raise AddonNotFoundInvalidManifest(str(e)) from e
        if not addon_dir.joinpath("__init__.py").is_file():
            raise AddonNotFoundNoInit(f"{addon_dir} is missing an __init__.py")
        return cls(manifest, manifest_path)
