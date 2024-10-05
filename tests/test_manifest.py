from typing import Any

import pytest

from manifestoo_core.manifest import InvalidManifest, Manifest


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("name", "the name"),
        ("name", None),
        ("version", "1.0.0"),
        ("version", None),
        ("license", "GPL-3"),
        ("license", None),
        ("development_status", "Beta"),
        ("development_status", None),
        ("depends", ["a", "b"]),
        ("external_dependencies", {"python": ["httpx"]}),
        ("installable", True),
        ("installable", False),
    ],
)
def test_manifest_valid_value(key: str, value: Any) -> None:
    manifest = Manifest.from_dict({key: value})
    assert getattr(manifest, key) == value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("name", 1),
        ("version", 1),
        ("license", ["i"]),
        ("development_status", {}),
        ("depends", 1),
        ("depends", {}),
        ("depends", None),
        ("external_dependencies", {1: {}}),
        ("external_dependencies", None),
        ("external_dependencies", [1]),
        ("installable", 1),
        ("installable", None),
    ],
)
def test_manifest_invalid_value(key: str, value: Any) -> None:
    manifest = Manifest.from_dict({key: value})
    with pytest.raises(InvalidManifest):
        getattr(manifest, key)


def test_manifest_non_str_keys() -> None:
    with pytest.raises(InvalidManifest):
        Manifest.from_dict({"name": "the name", 1: "1"})


def test_manifest_invalid_syntax() -> None:
    with pytest.raises(InvalidManifest):
        Manifest.from_str('{"name": "the name", ...}')


@pytest.mark.parametrize(
    ("key", "default"),
    [
        ("name", None),
        ("version", None),
        ("license", None),
        ("development_status", None),
        ("depends", []),
        ("external_dependencies", {}),
        ("installable", True),
        ("category", None),
    ],
)
def test_manifest_default_value(key: str, default: Any) -> None:
    manifest = Manifest.from_dict({})
    assert getattr(manifest, key) == default
