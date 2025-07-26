import email.parser
import re
import sys
import warnings
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from .addon import Addon
from .core_addons import get_core_addons
from .exceptions import (
    InvalidDistributionName,
    UnsupportedManifestVersion,
    UnsupportedOdooSeries,
)
from .git_postversion import (
    POST_VERSION_STRATEGY_DOT_N,
    POST_VERSION_STRATEGY_NINETYNINE_DEVN,
    POST_VERSION_STRATEGY_NONE,
    POST_VERSION_STRATEGY_P1_DEVN,
    get_git_postversion,
)
from .manifest import Manifest
from .odoo_series import MIN_VERSION_PARTS, OdooSeries

ODOO_ADDON_DIST_RE = re.compile(
    r"^(odoo(\d{1,2})?[-_]addon[-_].*|odoo$|odoo[^a-zA-Z0-9._-]+)",
    re.IGNORECASE,
)
ODOO_ADDON_METADATA_NAME_RE = re.compile(
    r"^odoo(\d{1,2})?[-_]addon[-_](?P<addon_name>[a-zA-Z0-9_-]+)$",
)

__all__ = [
    "POST_VERSION_STRATEGY_DOT_N",
    "POST_VERSION_STRATEGY_NINETYNINE_DEVN",
    "POST_VERSION_STRATEGY_NONE",
    "POST_VERSION_STRATEGY_P1_DEVN",
    "addon_name_to_distribution_name",
    "addon_name_to_requirement",
    "distribution_name_to_addon_name",
    "metadata_from_addon_dir",
]


def _filter_odoo_addon_dependencies(dependencies: Sequence[str]) -> Iterator[str]:
    """Filter a sequence of python packages dependencies to exclude 'odoo' and odoo
    addons."""
    for dependency in dependencies:
        if dependency.startswith("odoo>="):
            continue
        if ODOO_ADDON_DIST_RE.match(dependency):
            continue
        yield dependency


class MetadataOptions(TypedDict, total=False):
    """A dictionary of options for metadata conversion.

    Supported keys are:

    - ``depends_override``
    - ``external_dependencies_override``
    - ``external_dependencies_only``
    - ``odoo_series_override`` and ``odoo_version_override``
    - ``post_version_strategy_override``
    """

    depends_override: Optional[Dict[str, str]]
    external_dependencies_override: Optional[
        Dict[str, Dict[str, Union[str, List[str]]]]
    ]
    external_dependencies_only: Optional[bool]
    odoo_series_override: Optional[str]
    odoo_version_override: Optional[str]
    post_version_strategy_override: Optional[str]


def metadata_from_addon_dir(
    addon_dir: Path,
    options: Optional[MetadataOptions] = None,
    precomputed_metadata_file: Optional[Path] = None,
) -> Message:
    """Return Python Package Metadata 2.1 for an Odoo addon directory as an
    ``email.message.Message``.

    The Description field is absent and is stored in the message payload. All values are
    guaranteed to not contain newline characters, except for the payload.

    ``precomputed_metadata_path`` may point to a file containing pre-computed metadata
    that will be used to obtain the Name and Version, instead of looking at the addon
    directory name or manifest version + VCS, respectively. This is useful to process a
    manifest from a sdist tarball with PKG-INFO, for example, when the original
    directory name or VCS is not available to compute the package name and version.

    This function may raise :class:`manifestoo_core.exceptions.ManifestooException` if
    ``addon_dir`` does not contain a valid installable Odoo addon for a supported Odoo
    version.
    """
    if options is None:
        options = MetadataOptions()
    addon = Addon.from_addon_dir(addon_dir)
    manifest = addon.manifest

    if precomputed_metadata_file and precomputed_metadata_file.is_file():
        with precomputed_metadata_file.open(encoding="utf-8") as fp:
            pkg_info = email.parser.HeaderParser().parse(fp)
            addon_name = distribution_name_to_addon_name(pkg_info["Name"])
            version = pkg_info["Version"]
        _, odoo_series, odoo_series_info = _get_version(
            addon,
            options.get("odoo_series_override") or options.get("odoo_version_override"),
            git_post_version=False,
        )
    else:
        addon_name = addon_dir.absolute().name
        version, odoo_series, odoo_series_info = _get_version(
            addon,
            options.get("odoo_series_override") or options.get("odoo_version_override"),
            git_post_version=True,
            post_version_strategy_override=options.get(
                "post_version_strategy_override",
            ),
        )
    install_requires = _get_install_requires(
        odoo_series_info,
        manifest,
        depends_override=options.get("depends_override"),
        external_dependencies_override=options.get("external_dependencies_override"),
    )
    # Update Requires-Dist metadata with dependencies that are not odoo nor odoo addons
    if options.get("external_dependencies_only"):
        install_requires = list(_filter_odoo_addon_dependencies(install_requires))

    def _set(key: str, value: Union[None, str, List[str]]) -> None:
        if not value:
            return
        if isinstance(value, list):
            for v in value:
                meta[key] = v
        else:
            meta[key] = value

    meta = Message()
    _set("Metadata-Version", "2.1")
    _set("Name", _addon_name_to_metadata_name(addon_name, odoo_series_info))
    _set("Version", version)
    _set("Requires-Python", odoo_series_info.python_requires)
    _set("Requires-Dist", install_requires)
    _set("Summary", _no_nl(manifest.summary or manifest.name))
    _set("Home-page", manifest.website)
    _set("License", manifest.license)
    _set("Author", _no_nl(manifest.author))
    _set("Author-email", _author_email(manifest.author))
    _set("Classifier", _make_classifiers(odoo_series, manifest))
    long_description, long_description_content_type = _long_description(addon)
    if long_description:
        meta.set_payload(long_description)
    if long_description_content_type:
        _set("Description-Content-Type", long_description_content_type)

    return meta


@dataclass
class OdooSeriesInfo:
    odoo_dep: str
    pkg_name_pfx: str
    python_requires: str
    universal_wheel: bool
    git_postversion_strategy: str
    core_addons: Set[str]
    pkg_version_specifier: str = ""
    addons_ns: Optional[str] = None
    namespace_packages: Optional[List[str]] = None

    @classmethod
    def from_odoo_series(
        cls,
        odoo_series: OdooSeries,
        context: Optional[str] = None,
    ) -> "OdooSeriesInfo":
        try:
            return ODOO_SERIES_INFO[odoo_series]
        except KeyError as e:
            msg = "Unsupported odoo series '{odoo_series_str}'"
            if context:
                msg = f"{msg} in {context}"
            raise UnsupportedOdooSeries(msg) from e


ODOO_SERIES_INFO = {
    OdooSeries.v8_0: OdooSeriesInfo(
        odoo_dep="odoo>=8.0a,<9.0a",
        pkg_name_pfx="odoo8-addon",
        addons_ns="odoo_addons",
        namespace_packages=["odoo_addons"],
        python_requires="~=2.7",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        core_addons=get_core_addons(OdooSeries.v8_0),
    ),
    OdooSeries.v9_0: OdooSeriesInfo(
        odoo_dep="odoo>=9.0a,<9.1a",
        pkg_name_pfx="odoo9-addon",
        addons_ns="odoo_addons",
        namespace_packages=["odoo_addons"],
        python_requires="~=2.7",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        core_addons=get_core_addons(OdooSeries.v9_0),
    ),
    OdooSeries.v10_0: OdooSeriesInfo(
        odoo_dep="odoo>=10.0,<10.1dev",
        pkg_name_pfx="odoo10-addon",
        addons_ns="odoo.addons",
        namespace_packages=["odoo", "odoo.addons"],
        python_requires="~=2.7",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        core_addons=get_core_addons(OdooSeries.v10_0),
    ),
    OdooSeries.v11_0: OdooSeriesInfo(
        odoo_dep="odoo>=11.0a,<11.1dev",
        pkg_name_pfx="odoo11-addon",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
        universal_wheel=True,
        git_postversion_strategy=POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        core_addons=get_core_addons(OdooSeries.v11_0),
    ),
    OdooSeries.v12_0: OdooSeriesInfo(
        odoo_dep="odoo>=12.0a,<12.1dev",
        pkg_name_pfx="odoo12-addon",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.5",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_NINETYNINE_DEVN,
        core_addons=get_core_addons(OdooSeries.v12_0),
    ),
    OdooSeries.v13_0: OdooSeriesInfo(
        odoo_dep="odoo>=13.0a,<13.1dev",
        pkg_name_pfx="odoo13-addon",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.5",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_P1_DEVN,
        core_addons=get_core_addons(OdooSeries.v13_0),
    ),
    OdooSeries.v14_0: OdooSeriesInfo(
        odoo_dep="odoo>=14.0a,<14.1dev",
        pkg_name_pfx="odoo14-addon",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.6",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_P1_DEVN,
        core_addons=get_core_addons(OdooSeries.v14_0),
    ),
    OdooSeries.v15_0: OdooSeriesInfo(
        odoo_dep="odoo>=15.0a,<15.1dev",
        pkg_name_pfx="odoo-addon",
        pkg_version_specifier=">=15.0dev,<15.1dev",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.8",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_DOT_N,
        core_addons=get_core_addons(OdooSeries.v15_0),
    ),
    OdooSeries.v16_0: OdooSeriesInfo(
        odoo_dep="odoo>=16.0a,<16.1dev",
        pkg_name_pfx="odoo-addon",
        pkg_version_specifier=">=16.0dev,<16.1dev",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.10",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_DOT_N,
        core_addons=get_core_addons(OdooSeries.v16_0),
    ),
    OdooSeries.v17_0: OdooSeriesInfo(
        odoo_dep="odoo>=17.0a,<17.1dev",
        pkg_name_pfx="odoo-addon",
        pkg_version_specifier=">=17.0dev,<17.1dev",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.10",
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_DOT_N,
        core_addons=get_core_addons(OdooSeries.v17_0),
    ),
    OdooSeries.v18_0: OdooSeriesInfo(
        odoo_dep="odoo==18.0.*",
        pkg_name_pfx="odoo-addon",
        pkg_version_specifier="==18.0.*",
        addons_ns="odoo.addons",
        namespace_packages=None,
        python_requires=">=3.10",  # TODO To be confirmed
        universal_wheel=False,
        git_postversion_strategy=POST_VERSION_STRATEGY_DOT_N,
        core_addons=get_core_addons(OdooSeries.v18_0),
    ),
}

# map names of common python external dependencies in Odoo manifest files
# to actual python package names
EXTERNAL_DEPENDENCIES_MAP = {
    "Asterisk": "py-Asterisk",
    "coda": "pycoda",
    "cups": "pycups",
    "dateutil": "python-dateutil",
    "ldap": "python-ldap",
    "serial": "pyserial",
    "suds": "suds-jurko",
    "stdnum": "python-stdnum",
    "Crypto.Cipher.DES3": "pycrypto",
    "OpenSSL": "pyOpenSSL",
}


def distribution_name_to_addon_name(metadata_name: str) -> str:
    """Convert a packaging distribution name to the corresponding Odoo addon name."""
    mo = ODOO_ADDON_METADATA_NAME_RE.match(metadata_name)
    if not mo:
        msg = f"{metadata_name} does not look like an Odoo addon package name"
        raise InvalidDistributionName(msg)
    # Replacing '-' with '_' is not really useful, because the
    # `addon_name_to_distribution_name` does not replace '_' with '-'. But it is
    # kept for backward compatibility. If other normalizations such as
    # lowercasing had been applied, this would not yield the correct addon name.
    return mo.group("addon_name").replace("-", "_")


def _addon_name_to_metadata_name(
    addon_name: str,
    odoo_series_info: OdooSeriesInfo,
) -> str:
    return odoo_series_info.pkg_name_pfx + "-" + addon_name


def addon_name_to_distribution_name(addon_name: str, odoo_series: OdooSeries) -> str:
    """Convert an Odoo addon name to the corresponding packaging distribution name."""
    return _addon_name_to_metadata_name(
        addon_name,
        OdooSeriesInfo.from_odoo_series(odoo_series),
    )


def _addon_name_to_requires_dist(
    addon_name: str,
    odoo_series_info: OdooSeriesInfo,
) -> str:
    pkg_name = _addon_name_to_metadata_name(addon_name, odoo_series_info)
    pkg_version_specifier = odoo_series_info.pkg_version_specifier
    return pkg_name + pkg_version_specifier


def addon_name_to_requirement(addon_name: str, odoo_series: OdooSeries) -> str:
    """Convert an Odoo addon name to a requirement specifier."""
    return _addon_name_to_requires_dist(
        addon_name,
        OdooSeriesInfo.from_odoo_series(odoo_series),
    )


def _author_email(author: Optional[str]) -> Optional[str]:
    if author and "Odoo Community Association (OCA)" in author:
        return "support@odoo-community.org"
    return None


def _no_nl(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    return " ".join(s.split())


def _long_description(addon: Addon) -> Tuple[Optional[str], Optional[str]]:
    """
    :return: a tuple with long description and its content type
    """
    readme_path = addon.path / "README.rst"
    if readme_path.is_file():
        return readme_path.read_text(encoding="utf-8"), "text/x-rst"
    readme_path = addon.path / "README.md"
    if readme_path.is_file():
        return readme_path.read_text(encoding="utf-8"), "text/markdown"
    readme_path = addon.path / "README.txt"
    if readme_path.is_file():
        return readme_path.read_text(encoding="utf-8"), "text/plain"
    return addon.manifest.description, "text/x-rst"


def _make_classifiers(odoo_series: OdooSeries, manifest: Manifest) -> List[str]:
    classifiers = [
        "Programming Language :: Python",
        "Framework :: Odoo",
        f"Framework :: Odoo :: {odoo_series.value}",
    ]

    # commonly used licenses in OCA
    licenses = {
        "agpl-3": "License :: OSI Approved :: GNU Affero General Public License v3",
        "agpl-3 or any later version": (
            "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)"
        ),
        "gpl-2": "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "gpl-2 or any later version": (
            "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)"
        ),
        "gpl-3": "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "gpl-3 or any later version": (
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
        ),
        "lgpl-2": (
            "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)"
        ),
        "lgpl-2 or any later version": (
            "License :: OSI Approved :: "
            "GNU Lesser General Public License v2 or later (LGPLv2+)"
        ),
        "lgpl-3": (
            "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)"
        ),
        "lgpl-3 or any later version": (
            "License :: OSI Approved :: "
            "GNU Lesser General Public License v3 or later (LGPLv3+)"
        ),
    }
    license = manifest.license  # `license` is shadowing a python builtin
    if license:
        license_classifier = licenses.get(license.lower())
        if license_classifier:
            classifiers.append(license_classifier)

    # commonly used development status in OCA
    development_statuses = {
        "alpha": "Development Status :: 3 - Alpha",
        "beta": "Development Status :: 4 - Beta",
        "production/stable": "Development Status :: 5 - Production/Stable",
        "stable": "Development Status :: 5 - Production/Stable",
        "production": "Development Status :: 5 - Production/Stable",
        "mature": "Development Status :: 6 - Mature",
    }
    development_status = manifest.development_status
    if development_status:
        development_status_classifer = development_statuses.get(
            development_status.lower(),
        )
        if development_status_classifer:
            classifiers.append(development_status_classifer)

    return classifiers


def _get_install_requires(
    odoo_series_info: OdooSeriesInfo,
    manifest: Manifest,
    no_depends: Optional[Set[str]] = None,
    depends_override: Optional[Dict[str, str]] = None,
    external_dependencies_override: Optional[
        Dict[str, Dict[str, Union[str, List[str]]]]
    ] = None,
) -> List[str]:
    install_requires = []
    # dependency on Odoo
    install_requires.append(odoo_series_info.odoo_dep)
    # dependencies on other addons (except Odoo official addons)
    for depend in manifest.depends:
        if depend in odoo_series_info.core_addons:
            continue
        if no_depends and depend in no_depends:
            continue
        if depends_override and depend in depends_override:
            install_require = depends_override[depend]
        else:
            install_require = _addon_name_to_requires_dist(depend, odoo_series_info)
        if install_require:
            install_requires.append(install_require)
    # python external_dependencies
    for dep in manifest.external_dependencies.get("python", []):
        if external_dependencies_override and dep in external_dependencies_override.get(
            "python", {}
        ):
            final_dep = external_dependencies_override.get("python", {})[dep]
        else:
            final_dep = EXTERNAL_DEPENDENCIES_MAP.get(dep, dep)
        if isinstance(final_dep, list):
            install_requires.extend(final_dep)
        else:
            install_requires.append(final_dep)
    return sorted(install_requires)


def _get_version(
    addon: Addon,
    odoo_series_override: Optional[str] = None,
    git_post_version: bool = True,
    post_version_strategy_override: Optional[str] = None,
) -> Tuple[str, OdooSeries, OdooSeriesInfo]:
    """Get addon version information from an addon directory"""
    version = addon.manifest.version
    if not version:
        msg = f"No version in manifest in {addon.path}"
        warnings.warn(msg, stacklevel=1)
        version = "0.0.0"
    if not odoo_series_override:
        version_parts = version.split(".")
        if len(version_parts) < MIN_VERSION_PARTS:
            msg = (
                f"Version in manifest must have at least "
                f"{MIN_VERSION_PARTS} components and start with "
                f"the Odoo series number (in {addon.path})"
            )
            raise UnsupportedManifestVersion(msg)
        odoo_series_str = ".".join(version_parts[:2])
    else:
        odoo_series_str = odoo_series_override
    odoo_series = OdooSeries.from_str(
        odoo_series_str,
        context=str(addon.path),
    )
    odoo_series_info = OdooSeriesInfo.from_odoo_series(
        odoo_series,
        context=str(addon.path),
    )
    if git_post_version:
        version = get_git_postversion(
            addon,
            post_version_strategy_override or odoo_series_info.git_postversion_strategy,
        )
    return version, odoo_series, odoo_series_info
