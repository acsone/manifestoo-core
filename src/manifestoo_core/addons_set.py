import logging
from pathlib import Path
from typing import Dict, Iterable

from .addon import Addon
from .exceptions import AddonNotFound

_logger = logging.getLogger(__name__)


class AddonsSet(Dict[str, Addon]):
    def __str__(self) -> str:
        return ",".join(sorted(self.keys()))

    def add_from_addons_dir(self, addons_dir: Path) -> None:
        if not addons_dir.is_dir():
            _logger.warning(f"ignoring {addons_dir}: not a directory")
            return
        for addon_dir in addons_dir.iterdir():
            try:
                addon = Addon.from_addon_dir(addon_dir)
            except AddonNotFound as e:  # noqa: PERF203
                _logger.debug(f"ignoring {addon_dir}: {e}")
                continue
            else:
                self[addon.name] = addon

    def add_from_addons_dirs(self, addons_dirs: Iterable[Path]) -> None:
        for addons_dir in addons_dirs:
            self.add_from_addons_dir(addons_dir)
