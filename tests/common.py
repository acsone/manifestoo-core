from pathlib import Path
from typing import Any, Dict

from manifestoo_core.addon import Addon
from manifestoo_core.addons_set import AddonsSet
from manifestoo_core.manifest import Manifest


def populate_addons_dir(addons_dir: Path, addons: Dict[str, Dict[str, Any]]) -> None:
    if not addons_dir.is_dir():
        addons_dir.mkdir()
    for addon_name, manifest in addons.items():
        addon_path = addons_dir / addon_name
        addon_path.mkdir()
        (addon_path / "__init__.py").touch()
        manifest_path = addon_path / "__manifest__.py"
        manifest_path.write_text(repr(manifest))


def mock_addons_set(addons: Dict[str, Dict[str, Any]]) -> AddonsSet:
    addons_set = AddonsSet()
    for addon_name, manifest_dict in addons.items():
        manifest = Manifest.from_dict(manifest_dict)
        manifest_path = (
            Path("/tmp/fake-addons-dir") / addon_name / "__manifest__.py"  # noqa: S108
        )
        addons_set[addon_name] = Addon(manifest, manifest_path)
    return addons_set
