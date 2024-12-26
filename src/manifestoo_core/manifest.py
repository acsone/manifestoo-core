import ast
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .exceptions import InvalidManifest

T = TypeVar("T")
VT = TypeVar("VT")

__all__ = ["MANIFEST_NAMES", "InvalidManifest", "Manifest", "get_manifest_path"]

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


def _check_str(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError
    return value


def _check_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return value
    return _check_str(value)


def _check_bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError
    return value


def _check_list(value: Any, item_checker: Callable[[Any], T]) -> List[T]:
    if not isinstance(value, list):
        raise TypeError
    map(item_checker, value)
    return value


def _check_dict(
    value: Any,
    key_checker: Callable[[Any], T],
    value_checker: Callable[[Any], VT],
) -> Dict[T, VT]:
    if not isinstance(value, dict):
        raise TypeError
    for k, v in value.items():
        key_checker(k)
        value_checker(v)
    return value


def _check_list_of_str(value: Any) -> List[str]:
    # this could be a partial but mypy does not support it
    return _check_list(value, item_checker=_check_str)


def _check_dict_of_list_of_str(value: Any) -> Dict[str, List[str]]:
    # this could be a partial but mypy does not support it
    return _check_dict(value, key_checker=_check_str, value_checker=_check_list_of_str)


def get_manifest_path(addon_dir: Path) -> Optional[Path]:
    """Get the path to the manifest file for an addon directory.

    Returns None if no manifest file is found.
    """
    for manifest_name in MANIFEST_NAMES:
        manifest_path = addon_dir / manifest_name
        if manifest_path.is_file():
            return manifest_path
    return None


class Manifest:
    """Represent an Odoo manifest file."""

    def __init__(self, manifest_dict: Dict[str, Any]) -> None:
        """Do not use this contructor, use the from_* classmethods instead."""
        self.manifest_dict = manifest_dict

    def _get(self, key: str, checker: Callable[[Any], T], default: T) -> T:
        """Get value with runtime type check."""
        try:
            value = self.manifest_dict[key]
        except KeyError:
            return default
        try:
            return checker(value)
        except TypeError as e:
            msg = f"{value!r} has invalid type for {key!r} in {self}"
            raise InvalidManifest(msg) from e

    @property
    def name(self) -> Optional[str]:
        """The name field."""
        return self._get("name", _check_optional_str, default=None)

    @property
    def summary(self) -> Optional[str]:
        """The value of the summary field."""
        return self._get("summary", _check_optional_str, default=None)

    @property
    def description(self) -> Optional[str]:
        """The value of the description field."""
        return self._get("description", _check_optional_str, default=None)

    @property
    def version(self) -> Optional[str]:
        """The value of the version field."""
        return self._get("version", _check_optional_str, default=None)

    @property
    def installable(self) -> bool:
        """The value of the installable field if set, else True."""
        return self._get("installable", _check_bool, default=True)

    @property
    def depends(self) -> List[str]:
        """The value of the depends field if set, else []."""
        return self._get("depends", _check_list_of_str, default=[])

    @property
    def external_dependencies(self) -> Dict[str, List[str]]:
        """The value of the external_dependencies field if set, else {}."""
        return self._get(
            "external_dependencies",
            _check_dict_of_list_of_str,
            default={},
        )

    @property
    def license(self) -> Optional[str]:
        """The value of the license field."""
        return self._get("license", _check_optional_str, default=None)

    @property
    def author(self) -> Optional[str]:
        """The value of the author field."""
        return self._get("author", _check_optional_str, default=None)

    @property
    def category(self) -> Optional[str]:
        """The value of the category field."""
        return self._get("category", _check_optional_str, default=None)

    @property
    def website(self) -> Optional[str]:
        """The value of the website field."""
        return self._get("website", _check_optional_str, default=None)

    @property
    def development_status(self) -> Optional[str]:
        """The value of the development_status field."""
        return self._get("development_status", _check_optional_str, default=None)

    @classmethod
    def from_dict(
        cls,
        manifest_dict: Dict[Any, Any],
        source: str = "<manifest>",
    ) -> "Manifest":
        """Parse a manifest dictionary into a :class:`Manifest` object.

        Raises :class:`InvalidManifest` if the manifest is invalid.
        """
        if not isinstance(manifest_dict, dict):
            msg = f"Manifest {source} is not a dictionary"
            raise InvalidManifest(msg)
        if any(not isinstance(k, str) for k in manifest_dict):
            msg = f"Manifest {source} has non-string keys"
            raise InvalidManifest(msg)
        return cls(manifest_dict)

    @classmethod
    def from_str(cls, manifest_str: str, source: str = "<manifest>") -> "Manifest":
        """Parse a manifest string into a :class:`Manifest` object.

        Raises :class:`InvalidManifest` if the manifest is invalid.
        """
        try:
            manifest_dict = ast.literal_eval(manifest_str)
        except SyntaxError as e:
            msg = f"Manifest {source} has invalid syntax"
            raise InvalidManifest(msg) from e
        return cls.from_dict(manifest_dict)

    @classmethod
    def from_file(cls, manifest_path: Path) -> "Manifest":
        """Parse a manifest file into a :class:`Manifest` object.

        Raises :class:`InvalidManifest` if the manifest is invalid.
        """
        manifest_str = manifest_path.read_text()
        return cls.from_str(manifest_str, source=f"{manifest_path!r}")
