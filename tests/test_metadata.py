import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest
from pkg_metadata import msg_to_json

from manifestoo_core.exceptions import (
    InvalidDistributionName,
    UnsupportedManifestVersion,
    UnsupportedOdooSeries,
)
from manifestoo_core.metadata import (
    POST_VERSION_STRATEGY_DOT_N,
    POST_VERSION_STRATEGY_NINETYNINE_DEVN,
    POST_VERSION_STRATEGY_NONE,
    POST_VERSION_STRATEGY_P1_DEVN,
    _author_email,
    _filter_odoo_addon_dependencies,
    _no_nl,
    addon_name_to_distribution_name,
    addon_name_to_requirement,
    distribution_name_to_addon_name,
    metadata_from_addon_dir,
)
from manifestoo_core.odoo_series import OdooSeries


def _no_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _m(  # noqa: PLR0913 too many arguments
    tmp_path: Path,
    *,
    addon_dir_name: str = "addon1",
    # manifest
    name: Optional[str] = "Addon 1",
    version: str = "14.0.1.0.0",
    summary: Optional[str] = None,
    description: Optional[str] = None,
    readme_rst: Optional[str] = None,
    readme_md: Optional[str] = None,
    depends: Optional[List[str]] = None,
    external_dependencies: Optional[Dict[str, List[str]]] = None,
    website: Optional[str] = None,
    author: Optional[str] = None,
    license: Optional[str] = None,
    development_status: Optional[str] = None,
    # options
    depends_override: Optional[Dict[str, str]] = None,
    external_dependencies_override: Optional[
        Dict[str, Dict[str, Union[str, List[str]]]]
    ] = None,
    external_dependencies_only: Optional[bool] = None,
    odoo_series_override: Optional[str] = None,
    odoo_version_override: Optional[str] = None,
    post_version_strategy_override: Optional[str] = None,
    precomputed_metadata_file: Optional[Path] = None,
) -> Dict[str, Any]:
    addon_dir = tmp_path / addon_dir_name
    addon_dir.mkdir()
    addon_dir.joinpath("__init__.py").touch()
    manifest_path = addon_dir / "__manifest__.py"
    manifest_path.write_text(
        repr(
            _no_none(
                {
                    "name": name,
                    "version": version,
                    "summary": summary,
                    "description": description,
                    "depends": depends,
                    "external_dependencies": external_dependencies,
                    "website": website,
                    "author": author,
                    "license": license,
                    "development_status": development_status,
                },
            ),
        ),
    )
    if readme_rst:
        readme_path = addon_dir / "README.rst"
        readme_path.write_text(readme_rst)
    if readme_md:
        readme_path = addon_dir / "README.md"
        readme_path.write_text(readme_md)
    return msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={
                "depends_override": depends_override,
                "external_dependencies_override": external_dependencies_override,
                "external_dependencies_only": external_dependencies_only,
                "odoo_series_override": odoo_series_override,
                "odoo_version_override": odoo_version_override,
                "post_version_strategy_override": post_version_strategy_override,
            },
            precomputed_metadata_file=precomputed_metadata_file,
        ),
    )


def test_basic(tmp_path: Path) -> None:
    assert _m(tmp_path) == {
        "name": "odoo14-addon-addon1",
        "version": "14.0.1.0.0",
        "summary": "Addon 1",
        "requires_dist": ["odoo>=14.0a,<14.1dev"],
        "requires_python": ">=3.6",
        "classifier": [
            "Programming Language :: Python",
            "Framework :: Odoo",
            "Framework :: Odoo :: 14.0",
        ],
        "metadata_version": "2.1",
        "description_content_type": "text/x-rst",
    }


def test_no_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/foo")  # make sure git is not in PATH
    assert (
        _m(tmp_path, post_version_strategy_override=POST_VERSION_STRATEGY_NONE)[
            "version"
        ]
        == "14.0.1.0.0"
    )


@pytest.mark.parametrize(
    ("odoo_series", "expected"),
    [
        ("8.0", ["odoo>=8.0a,<9.0a"]),
        ("9.0", ["odoo>=9.0a,<9.1a"]),
        ("10.0", ["odoo>=10.0,<10.1dev"]),
        ("11.0", ["odoo>=11.0a,<11.1dev"]),
        ("12.0", ["odoo>=12.0a,<12.1dev"]),
        ("13.0", ["odoo>=13.0a,<13.1dev"]),
        ("14.0", ["odoo>=14.0a,<14.1dev"]),
        ("15.0", ["odoo>=15.0a,<15.1dev"]),
        ("16.0", ["odoo>=16.0a,<16.1dev"]),
    ],
)
def test_requires_odoo(tmp_path: Path, odoo_series: str, expected: List[str]) -> None:
    assert _m(tmp_path, version=f"{odoo_series}.1.0.0")["requires_dist"] == expected


@pytest.mark.parametrize(
    ("odoo_series", "expected"),
    [
        ("8.0", "~=2.7"),
        ("9.0", "~=2.7"),
        ("10.0", "~=2.7"),
        ("11.0", ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"),
        ("12.0", ">=3.5"),
        ("13.0", ">=3.5"),
        ("14.0", ">=3.6"),
        ("15.0", ">=3.8"),
        ("16.0", ">=3.10"),
    ],
)
def test_requires_python(tmp_path: Path, odoo_series: str, expected: str) -> None:
    assert _m(tmp_path, version=f"{odoo_series}.1.0.0")["requires_python"] == expected


@pytest.mark.parametrize(
    ("odoo_series", "expected_prefix"),
    [
        ("8.0", "odoo8-addon-"),
        ("9.0", "odoo9-addon-"),
        ("10.0", "odoo10-addon-"),
        ("11.0", "odoo11-addon-"),
        ("12.0", "odoo12-addon-"),
        ("13.0", "odoo13-addon-"),
        ("14.0", "odoo14-addon-"),
        ("15.0", "odoo-addon-"),
        ("16.0", "odoo-addon-"),
    ],
)
def test_name_prefix(tmp_path: Path, odoo_series: str, expected_prefix: str) -> None:
    assert (
        _m(tmp_path, name="addon1", version=f"{odoo_series}.1.0.0")["name"]
        == f"{expected_prefix}addon1"
    )


def test_depends_core_addon(tmp_path: Path) -> None:
    """A dependency on a core addon should be ignored."""
    assert _m(tmp_path, version="14.0.1.0.0", depends=["base"])["requires_dist"] == [
        "odoo>=14.0a,<14.1dev",
    ]


@pytest.mark.parametrize(
    ("odoo_series", "depends", "expected"),
    [
        ("8.0", ["mis_builder"], ["odoo8-addon-mis_builder"]),
        ("9.0", ["mis_builder"], ["odoo9-addon-mis_builder"]),
        ("10.0", ["mis_builder"], ["odoo10-addon-mis_builder"]),
        ("11.0", ["mis_builder"], ["odoo11-addon-mis_builder"]),
        ("12.0", ["mis_builder"], ["odoo12-addon-mis_builder"]),
        ("13.0", ["mis_builder"], ["odoo13-addon-mis_builder"]),
        ("14.0", ["mis_builder"], ["odoo14-addon-mis_builder"]),
        ("15.0", ["mis_builder"], ["odoo-addon-mis_builder>=15.0dev,<15.1dev"]),
        ("16.0", ["mis_builder"], ["odoo-addon-mis_builder>=16.0dev,<16.1dev"]),
        (
            "14.0",
            [
                "mis_builder",
                "mis_builder_budget",
            ],
            [
                "odoo14-addon-mis_builder",
                "odoo14-addon-mis_builder_budget",
            ],
        ),
        (
            "16.0",
            [
                "base",
                "mis_builder",
                "mis_builder_budget",
            ],
            [
                "odoo-addon-mis_builder>=16.0dev,<16.1dev",
                "odoo-addon-mis_builder_budget>=16.0dev,<16.1dev",
            ],
        ),
    ],
)
def test_depends_noncore_addon(
    tmp_path: Path,
    odoo_series: str,
    depends: List[str],
    expected: List[str],
) -> None:
    """A dependency on a non-core addon appears in requires_dist."""
    requires_dist = _m(tmp_path, version=f"{odoo_series}.1.0.0", depends=depends)[
        "requires_dist"
    ]
    assert [d for d in requires_dist if not d.startswith("odoo>=")] == expected


def test_depends_override(tmp_path: Path) -> None:
    """A dependency on a non-core addon appears in requires_dist."""
    assert _m(
        tmp_path,
        depends=["mis_builder"],
        depends_override={"mis_builder": "odoo14-addon-mis_builder>=14.0.4.0.0"},
    )["requires_dist"] == [
        "odoo14-addon-mis_builder>=14.0.4.0.0",
        "odoo>=14.0a,<14.1dev",
    ]


def test_external_dependencies(tmp_path: Path) -> None:
    assert _m(tmp_path, external_dependencies={"python": ["lxml"]})[
        "requires_dist"
    ] == [
        "lxml",
        "odoo>=14.0a,<14.1dev",
    ]


def test_external_dependencies_only(tmp_path: Path) -> None:
    assert _m(
        tmp_path,
        depends=["mis_builder"],
        external_dependencies={"python": ["lxml"]},
        external_dependencies_only=True,
    )["requires_dist"] == [
        "lxml",
    ]


def test_external_dependencies_override(tmp_path: Path) -> None:
    assert _m(
        tmp_path,
        external_dependencies={"python": ["lxml"]},
        external_dependencies_override={"python": {"lxml": "lxml>=3.8.0"}},
    )["requires_dist"] == [
        "lxml>=3.8.0",
        "odoo>=14.0a,<14.1dev",
    ]


def test_external_dependencies_override_multi(tmp_path: Path) -> None:
    assert _m(
        tmp_path,
        external_dependencies={"python": ["lxml"]},
        external_dependencies_override={
            "python": {"lxml": ["lxml>=3.8.0", "something"]},
        },
    )["requires_dist"] == ["lxml>=3.8.0", "odoo>=14.0a,<14.1dev", "something"]


def test_odoo_series_unsupported(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedOdooSeries):
        _m(tmp_path, version="45.0.1.0.0")


@pytest.mark.parametrize("version", ["1", "1.0", "1.0.0", "1.0.0.0", "10.0.0.0"])
def test_manifest_version_undetermined(tmp_path: Path, version: str) -> None:
    with pytest.raises(UnsupportedManifestVersion):
        _m(tmp_path, version=version)


def test_odoo_version_override(tmp_path: Path) -> None:
    assert _m(tmp_path, version="45.0.1.0.0", odoo_version_override="14.0")[
        "requires_dist"
    ] == ["odoo>=14.0a,<14.1dev"]


def test_odoo_series_override(tmp_path: Path) -> None:
    assert _m(tmp_path, version="45.0.1.0.0", odoo_series_override="14.0")[
        "requires_dist"
    ] == ["odoo>=14.0a,<14.1dev"]


def test_summary_defaults_to_name(tmp_path: Path) -> None:
    assert _m(tmp_path, name="addon1")["summary"] == "addon1"


def test_summary_from_summary(tmp_path: Path) -> None:
    assert _m(tmp_path, name="addon1", summary="Addon 1")["summary"] == "Addon 1"


def test_description(
    tmp_path: Path,
    description: str = "A description\n\nwith two lines",
) -> None:
    assert _m(tmp_path, description=description)["description"] == description


def test_description_from_readme(
    tmp_path: Path,
    readme_rst: str = "A readme\n\nwith two lines",
) -> None:
    m = _m(tmp_path, readme_rst=readme_rst)
    assert m["description"] == readme_rst
    assert m["description_content_type"] == "text/x-rst"


def test_description_from_readme_md(
    tmp_path: Path,
    readme_md: str = "A readme\n\nwith two lines",
) -> None:
    m = _m(tmp_path, readme_md=readme_md)
    assert m["description"] == readme_md
    assert m["description_content_type"] == "text/markdown"


def test_description_from_description_and_readme(
    tmp_path: Path,
    description: str = "A description",
    readme_rst: str = "A readme\n\nwith two lines",
) -> None:
    m = _m(tmp_path, description=description, readme_rst=readme_rst)
    assert m["description"] == readme_rst
    assert m["description_content_type"] == "text/x-rst"


def test_author(tmp_path: Path) -> None:
    assert _m(tmp_path, author="John Doe")["author"] == "John Doe"


def test_author_no_nl(tmp_path: Path) -> None:
    assert _m(tmp_path, author="John Doe,\nOCA")["author"] == "John Doe, OCA"


def test_author_email_oca(tmp_path: Path) -> None:
    assert "author_email" not in _m(
        tmp_path,
        addon_dir_name="a",
        author="John Doe",
    )
    assert (
        _m(
            tmp_path,
            addon_dir_name="b",
            author="John Doe, Odoo Community Association (OCA)",
        )["author_email"]
        == "support@odoo-community.org"
    )


@pytest.mark.parametrize(
    "odoo_series",
    ["8.0", "9.0", "10.0", "11.0", "12.0", "13.0", "14.0", "15.0", "16.0"],
)
def test_classifiers(tmp_path: Path, odoo_series: str) -> None:
    assert _m(tmp_path, version=f"{odoo_series}.1.0.0")["classifier"] == [
        "Programming Language :: Python",
        "Framework :: Odoo",
        f"Framework :: Odoo :: {odoo_series}",
    ]


@pytest.mark.parametrize(
    ("license", "expected_license"),
    [
        (
            "agpl-3",
            "License :: OSI Approved :: GNU Affero General Public License v3",
        ),
        (
            "AGPL-3",
            "License :: OSI Approved :: GNU Affero General Public License v3",
        ),
        (
            "agpl-3 or any later version",
            "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)",
        ),
        (
            "gpl-2",
            "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        ),
        (
            "gpl-2 or any later version",
            "License :: OSI Approved :: "
            "GNU General Public License v2 or later (GPLv2+)",
        ),
        (
            "gpl-3",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        ),
        (
            "gpl-3 or any later version",
            "License :: OSI Approved :: "
            "GNU General Public License v3 or later (GPLv3+)",
        ),
        (
            "lgpl-2",
            "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
        ),
        (
            "lgpl-2 or any later version",
            "License :: OSI Approved :: "
            "GNU Lesser General Public License v2 or later (LGPLv2+)",
        ),
        (
            "lgpl-3",
            "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        ),
        (
            "lgpl-3 or any later version",
            "License :: OSI Approved :: "
            "GNU Lesser General Public License v3 or later (LGPLv3+)",
        ),
    ],
)
def test_classifiers_license(
    tmp_path: Path,
    license: str,  # shadowing Python builtin
    expected_license: str,
) -> None:
    assert expected_license in _m(tmp_path, license=license)["classifier"]


@pytest.mark.parametrize(
    ("development_status", "expected_development_status"),
    [
        ("alpha", "Development Status :: 3 - Alpha"),
        ("beta", "Development Status :: 4 - Beta"),
        ("production/stable", "Development Status :: 5 - Production/Stable"),
        ("stable", "Development Status :: 5 - Production/Stable"),
        ("production", "Development Status :: 5 - Production/Stable"),
        ("mature", "Development Status :: 6 - Mature"),
    ],
)
def test_classifiers_development_status(
    tmp_path: Path,
    development_status: str,
    expected_development_status: str,
) -> None:
    assert (
        expected_development_status
        in _m(tmp_path, development_status=development_status)["classifier"]
    )


def test_license(tmp_path: Path, license: str = "AGPL-3") -> None:
    assert _m(tmp_path, license=license)["license"] == license


def test_home_page(tmp_path: Path, website: str = "https://acsone.eu") -> None:
    assert _m(tmp_path, website=website)["home_page"] == website


def test_precomputed_metadata_path(tmp_path: Path) -> None:
    pkg_info_path = tmp_path / "PKG-INFO"
    pkg_info_path.write_text("Name: odoo14-addon-addon1\nVersion: 14.0.1.0.0.3")
    metadata = _m(
        tmp_path,
        addon_dir_name="tmp",
        version="14.0.1.0.0",
        precomputed_metadata_file=pkg_info_path,
    )
    assert metadata["name"] == "odoo14-addon-addon1"
    assert metadata["version"] == "14.0.1.0.0.3"


def _make_git_addon(
    tmp_path: Path,
    manifest_version: str,
    post_commits: int = 0,
    addon_name: str = "addon1",
) -> Path:
    addon_dir = tmp_path / addon_name
    addon_dir.mkdir()
    addon_dir.joinpath("__manifest__.py").write_text(
        f"{{'name': '{addon_name}', 'version': '{manifest_version}'}}",
    )
    addon_dir.joinpath("__init__.py").touch()
    subprocess.check_call(["git", "init"], cwd=addon_dir)
    subprocess.check_call(
        ["git", "config", "user.email", "test@example.com"],
        cwd=addon_dir,
    )
    subprocess.check_call(["git", "config", "user.name", "test"], cwd=addon_dir)
    subprocess.check_call(["git", "add", "."], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "initial commit"], cwd=addon_dir)
    for i in range(post_commits):
        addon_dir.joinpath("README.rst").write_text(f"{i}")
        subprocess.check_call(["git", "add", "README.rst"], cwd=addon_dir)
        subprocess.check_call(["git", "commit", "-m", f"commit {i}"], cwd=addon_dir)
    return addon_dir


@pytest.mark.parametrize(
    (
        "manifest_version",
        "post_commits",
        "post_version_strategy_override",
        "expected_version",
    ),
    [
        # last commit is manifest version change
        ("8.0.1.0.0", 0, None, "8.0.1.0.0"),
        ("9.0.1.0.0", 0, None, "9.0.1.0.0"),
        ("10.0.1.0.0", 0, None, "10.0.1.0.0"),
        ("11.0.1.0.0", 0, None, "11.0.1.0.0"),
        ("12.0.1.0.0", 0, None, "12.0.1.0.0"),
        ("13.0.1.0.0", 0, None, "13.0.1.0.0"),
        ("14.0.1.0.0", 0, None, "14.0.1.0.0"),
        ("15.0.1.0.0", 0, None, "15.0.1.0.0"),
        ("16.0.1.0.0", 0, None, "16.0.1.0.0"),
        # 2 commits after manifest version change
        ("8.0.1.0.0", 2, None, "8.0.1.0.0.99.dev2"),
        ("9.0.1.0.0", 2, None, "9.0.1.0.0.99.dev2"),
        ("10.0.1.0.0", 2, None, "10.0.1.0.0.99.dev2"),
        ("11.0.1.0.0", 2, None, "11.0.1.0.0.99.dev2"),
        ("12.0.1.0.0", 2, None, "12.0.1.0.0.99.dev2"),
        ("13.0.1.0.0", 2, None, "13.0.1.0.1.dev2"),
        ("14.0.1.0.0", 2, None, "14.0.1.0.1.dev2"),
        ("15.0.1.0.0", 2, None, "15.0.1.0.0.2"),
        ("16.0.1.0.0", 2, None, "16.0.1.0.0.2"),
        # strategy overrides
        ("16.0.1.0.0", 2, POST_VERSION_STRATEGY_NONE, "16.0.1.0.0"),
        ("16.0.1.0.0", 2, POST_VERSION_STRATEGY_NINETYNINE_DEVN, "16.0.1.0.0.99.dev2"),
        ("16.0.1.0.0", 2, POST_VERSION_STRATEGY_P1_DEVN, "16.0.1.0.1.dev2"),
        ("16.0.1.0.0", 2, POST_VERSION_STRATEGY_DOT_N, "16.0.1.0.0.2"),
    ],
)
def test_git_post_version(
    tmp_path: Path,
    manifest_version: str,
    post_commits: int,
    post_version_strategy_override: Optional[str],
    expected_version: str,
) -> None:
    addon_dir = _make_git_addon(
        tmp_path,
        manifest_version=manifest_version,
        post_commits=post_commits,
    )
    metadata = msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={"post_version_strategy_override": post_version_strategy_override},
        ),
    )
    assert metadata["version"] == expected_version


@pytest.mark.parametrize(
    (
        "manifest_version",
        "post_commits",
        "post_version_strategy_override",
        "expected_version",
    ),
    [
        ("16.0.1.0.0", 1, POST_VERSION_STRATEGY_NONE, "16.0.1.0.0"),
        ("16.0.1.0.0", 1, POST_VERSION_STRATEGY_NINETYNINE_DEVN, "16.0.1.0.0.99.dev2"),
        ("16.0.1.0.0", 1, POST_VERSION_STRATEGY_P1_DEVN, "16.0.1.0.1.dev2"),
        ("16.0.1.0.0", 1, POST_VERSION_STRATEGY_DOT_N, "16.0.1.0.0.2"),
    ],
)
def test_git_post_version_uncommitted_change(
    tmp_path: Path,
    manifest_version: str,
    post_commits: int,
    post_version_strategy_override: str,
    expected_version: str,
) -> None:
    addon_dir = _make_git_addon(
        tmp_path,
        manifest_version=manifest_version,
        post_commits=post_commits,
    )
    addon_dir.joinpath("README.rst").write_text("stuff")
    metadata = msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={"post_version_strategy_override": post_version_strategy_override},
        ),
    )
    assert metadata["version"] == expected_version


@pytest.mark.parametrize(
    "post_version_strategy_override",
    [
        POST_VERSION_STRATEGY_NONE,
        POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        POST_VERSION_STRATEGY_P1_DEVN,
        POST_VERSION_STRATEGY_DOT_N,
    ],
)
def test_git_post_version_bad_manifest_in_history(
    tmp_path: Path,
    post_version_strategy_override: str,
) -> None:
    addon_dir = _make_git_addon(tmp_path, manifest_version="16.0.1.1.0")
    addon_dir.joinpath("__manifest__.py").write_text(
        "{syntaxerror, 'version': '16.0.1.2.0'}",
    )
    subprocess.check_call(["git", "add", "__manifest__.py"], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "bad manifest"], cwd=addon_dir)
    addon_dir.joinpath("__manifest__.py").write_text(
        "{'name': 'A', 'version': '16.0.1.3.0'}",
    )
    subprocess.check_call(["git", "add", "__manifest__.py"], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "good manifest"], cwd=addon_dir)
    metadata = msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={"post_version_strategy_override": post_version_strategy_override},
        ),
    )
    assert metadata["version"] == "16.0.1.3.0"


@pytest.mark.parametrize(
    "post_version_strategy_override",
    [
        POST_VERSION_STRATEGY_NONE,
        POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        POST_VERSION_STRATEGY_P1_DEVN,
        POST_VERSION_STRATEGY_DOT_N,
    ],
)
def test_git_post_version_good_manifest_in_history(
    tmp_path: Path,
    post_version_strategy_override: str,
) -> None:
    addon_dir = _make_git_addon(tmp_path, manifest_version="16.0.1.1.0")
    addon_dir.joinpath("__manifest__.py").write_text(
        "{'name': 'A', 'version': '16.0.1.2.0'}",
    )
    subprocess.check_call(["git", "add", "__manifest__.py"], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "good manifest"], cwd=addon_dir)
    metadata = msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={"post_version_strategy_override": post_version_strategy_override},
        ),
    )
    assert metadata["version"] == "16.0.1.2.0"


@pytest.mark.parametrize(
    "post_version_strategy_override",
    [
        POST_VERSION_STRATEGY_NONE,
        POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        POST_VERSION_STRATEGY_P1_DEVN,
        POST_VERSION_STRATEGY_DOT_N,
    ],
)
def test_git_post_version_no_manifest_in_history(
    tmp_path: Path,
    post_version_strategy_override: str,
) -> None:
    addon_dir = _make_git_addon(tmp_path, manifest_version="16.0.1.1.0")
    subprocess.check_call(["git", "rm", "__manifest__.py"], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "no manifest"], cwd=addon_dir)
    addon_dir.joinpath("__manifest__.py").write_text(
        "{'name': 'A', 'version': '16.0.1.2.0'}",
    )
    subprocess.check_call(["git", "add", "__manifest__.py"], cwd=addon_dir)
    subprocess.check_call(["git", "commit", "-m", "good manifest"], cwd=addon_dir)
    metadata = msg_to_json(
        metadata_from_addon_dir(
            addon_dir,
            options={"post_version_strategy_override": post_version_strategy_override},
        ),
    )
    assert metadata["version"] == "16.0.1.2.0"


@pytest.mark.parametrize(
    ("dependencies", "expected"),
    [
        (
            [
                "lxml",
                "wrapt",
                "odoo8-addon-toto",
                "odoo12-addon-connector",
                "odoo",
                "odoo>=16",
                "odoo-addon-mis_builder",
                "odoorpc",
            ],
            ["lxml", "wrapt", "odoorpc"],
        ),
    ],
)
def test_filter_odoo_addon_dependencies(
    dependencies: List[str],
    expected: List[str],
) -> None:
    assert list(_filter_odoo_addon_dependencies(dependencies)) == expected


def test_distribution_name_to_addon_name() -> None:
    assert distribution_name_to_addon_name("odoo14-addon-addon1") == "addon1"
    assert distribution_name_to_addon_name("odoo-addon-addon1") == "addon1"
    assert distribution_name_to_addon_name("odoo-addon-addon-1") == "addon_1"
    assert distribution_name_to_addon_name("odoo-addon-addon_1") == "addon_1"
    assert distribution_name_to_addon_name("odoo-addon-aDDon_1") == "aDDon_1"
    with pytest.raises(InvalidDistributionName):
        distribution_name_to_addon_name("odoo14-addon-")
    with pytest.raises(InvalidDistributionName):
        distribution_name_to_addon_name("addon1")


def test_addon_name_to_distribution_name() -> None:
    assert (
        addon_name_to_distribution_name("addon1", OdooSeries.v14_0)
        == "odoo14-addon-addon1"
    )
    assert (
        addon_name_to_distribution_name("Addon_1", OdooSeries.v16_0)
        == "odoo-addon-Addon_1"
    )


def test_addon_name_to_requirement() -> None:
    assert (
        addon_name_to_requirement("addon1", OdooSeries.v14_0) == "odoo14-addon-addon1"
    )
    assert (
        addon_name_to_requirement("addon1", OdooSeries.v16_0)
        == "odoo-addon-addon1>=16.0dev,<16.1dev"
    )


def test_get_author_email() -> None:
    assert (
        _author_email("Odoo Community Association (OCA)")
        == "support@odoo-community.org"
    )
    assert (
        _author_email("Odoo Community Association (OCA), ACSONE SA/NV")
        == "support@odoo-community.org"
    )
    assert _author_email("ACSONE SA/NV") is None


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("", ""),
        (None, None),
        ("   ", ""),
        (" \n ", ""),
        ("a", "a"),
        ("   a\nb\n", "a b"),
    ],
)
def test_no_nl(s: Optional[str], expected: Optional[str]) -> None:
    assert _no_nl(s) == expected
