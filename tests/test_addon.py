from pathlib import Path

import pytest

from manifestoo_core.addon import Addon, is_addon_dir
from manifestoo_core.exceptions import (
    AddonNotFoundInvalidManifest,
    AddonNotFoundNoInit,
    AddonNotFoundNoManifest,
    AddonNotFoundNotADirectory,
    AddonNotFoundNotInstallable,
)
from manifestoo_core.manifest import Manifest


@pytest.fixture(
    params=[
        {
            "dir": "a",
            "manifest": "{}",
        },
    ],
)
def addon_dir(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    addon_dir = tmp_path.joinpath(request.param["dir"])
    addon_dir.mkdir()
    addon_dir.joinpath("__init__.py").touch()
    addon_dir.joinpath("__manifest__.py").write_text(request.param["manifest"])
    return addon_dir


@pytest.mark.parametrize(
    "addon_dir",
    [
        {
            "dir": "theaddon",
            "manifest": "{'name': 'the addon'}",
        },
    ],
    indirect=True,
)
def test_basic(addon_dir: Path) -> None:
    addon = Addon.from_addon_dir(addon_dir)
    assert addon.name == "theaddon"
    assert addon.path == addon_dir
    assert addon.manifest.name == "the addon"


def test_not_a_directory(tmp_path: Path) -> None:
    with pytest.raises(AddonNotFoundNotADirectory):
        Addon.from_addon_dir(tmp_path / "not-a-dir")


@pytest.mark.parametrize(
    "addon_dir",
    [
        {
            "dir": "a",
            "manifest": "{'installable': False}",
        },
    ],
    indirect=True,
)
def test_not_installable(addon_dir: Path) -> None:
    with pytest.raises(AddonNotFoundNotInstallable):
        Addon.from_addon_dir(addon_dir)
    assert Addon.from_addon_dir(addon_dir, allow_not_installable=True)


@pytest.mark.parametrize(
    "addon_dir",
    [
        {
            "dir": "a",
            "manifest": "[]",
        },
    ],
    indirect=True,
)
def test_invalid_manifest(addon_dir: Path) -> None:
    with pytest.raises(AddonNotFoundInvalidManifest):
        Addon.from_addon_dir(addon_dir)


@pytest.mark.parametrize(
    "addon_dir",
    [
        {
            "dir": "a",
            "manifest": "{'installable':}",
        },
    ],
    indirect=True,
)
def test_manifest_syntax_error(addon_dir: Path) -> None:
    with pytest.raises(AddonNotFoundInvalidManifest):
        Addon.from_addon_dir(addon_dir)


@pytest.mark.parametrize(
    "addon_dir",
    [
        {
            "dir": "a",
            "manifest": "{'installable': '?'}",
        },
    ],
    indirect=True,
)
def test_manifest_type_error(addon_dir: Path) -> None:
    with pytest.raises(AddonNotFoundInvalidManifest):
        Addon.from_addon_dir(addon_dir)


def test_no_manifest(addon_dir: Path) -> None:
    (addon_dir / "__manifest__.py").unlink()
    with pytest.raises(AddonNotFoundNoManifest):
        Addon.from_addon_dir(addon_dir)


def test_no_init(addon_dir: Path) -> None:
    (addon_dir / "__init__.py").unlink()
    with pytest.raises(AddonNotFoundNoInit):
        Addon.from_addon_dir(addon_dir)


def test_addon_constructor() -> None:
    manifest = Manifest.from_dict({"name": "the addon"})
    addon = Addon(
        manifest,
        manifest_path=Path("/tmp/theaddon/__manifest__.py"),  # noqa: S108
    )
    assert addon.name == "theaddon"
    addon = Addon(
        manifest,
        manifest_path=Path("/tmp/tmp/__manifest__.py"),  # noqa: S108
        name="theaddon",
    )
    assert addon.name == "theaddon"


@pytest.mark.parametrize(
    ("addon_dir", "expected"),
    [
        (
            {
                "dir": "a",
                "manifest": "{}",
            },
            True,
        ),
        (
            {
                "dir": "a",
                "manifest": "{'installable': '?'}",
            },
            False,
        ),
    ],
    indirect=["addon_dir"],
)
def test_is_addon_dir_ok(addon_dir: Path, expected: bool) -> None:
    assert is_addon_dir(addon_dir) is expected
