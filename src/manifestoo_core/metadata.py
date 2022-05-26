import sys
from email.message import Message
from pathlib import Path
from typing import Dict, List, Optional, Union

if sys.version_info >= (3, 8):
    from typing import Final, TypedDict
else:
    from typing_extensions import Final, TypedDict

from .exceptions import UnsupportedManifestVersion, UnsupportedOdooVersion

POST_VERSION_STRATEGY_NONE: Final = "none"
POST_VERSION_STRATEGY_NINETYNINE_DEVN: Final = ".99.devN"
POST_VERSION_STRATEGY_P1_DEVN: Final = "+1.devN"
POST_VERSION_STRATEGY_DOT_N: Final = ".N"


class MetadataOptions(TypedDict, total=False):
    """A dictionary of options for metadata conversion.

    Supported keys are:

    - ``depends_override``
    - ``external_dependencies_override``
    - ``odoo_version_override``
    - ``post_version_strategy_override``
    """

    depends_override: Optional[Dict[str, str]]
    external_dependencies_override: Optional[
        Dict[str, Dict[str, Union[str, List[str]]]]
    ]
    odoo_version_override: Optional[str]
    post_version_strategy_override: Optional[str]


def metadata_from_addon_dir(
    addon_dir: Path,
    options: Optional[MetadataOptions] = None,
    precomputed_metadata_file: Optional[Path] = None,
) -> Message:
    """Return Python Package Metadata 2.2 for an Odoo addon directory as an
    ``email.message.Message``.

    The Description field is absent and is stored in the message payload. All values are
    guaranteed to not contain newline characters, except for the payload.

    ``precomputed_metadata_path`` may point to a file containing pre-computed metadata
    that will be used to obtain the Name and Version, instead of looking at the addon
    directory name or manifest version + VCS, respectively. This is useful to process a
    manifest from a sdist tarball with PKG-INFO, for example, when then original
    directory name or VCS is not available to compute the package name and version.
    """
    return _metadata_from_addon_dir_using_setuptools_odoo(
        addon_dir,
        options or MetadataOptions(),
        precomputed_metadata_file,
    )


def _metadata_from_addon_dir_using_setuptools_odoo(
    addon_dir: Path,
    options: MetadataOptions,
    precomputed_metadata_file: Optional[Path] = None,
) -> Message:
    from distutils.errors import DistutilsSetupError

    from setuptools_odoo import get_addon_metadata  # type: ignore

    try:
        return get_addon_metadata(  # type: ignore
            str(addon_dir),
            depends_override=options.get("depends_override"),
            external_dependencies_override=options.get(
                "external_dependencies_override"
            ),
            odoo_version_override=options.get("odoo_version_override"),
            post_version_strategy_override=options.get(
                "post_version_strategy_override"
            ),
            precomputed_metadata_path=precomputed_metadata_file,
        )
    except DistutilsSetupError as e:
        if "Unsupported odoo version" in str(e):
            raise UnsupportedOdooVersion(str(e)) from e
        elif "Version in manifest must" in str(e):
            raise UnsupportedManifestVersion(str(e)) from e
        raise
