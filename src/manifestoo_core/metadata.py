import sys
from email.message import Message
from pathlib import Path
from typing import Dict, List, Optional, Union

if sys.version_info >= (3, 8):
    from typing import Final, TypedDict
else:
    from typing_extensions import Final, TypedDict

from .manifest import Manifest


class UnsupportedOdooVersion(Exception):
    pass


class UnsupportedManifestVersion(Exception):
    pass


POST_VERSION_STRATEGY_NONE: Final = "none"
POST_VERSION_STRATEGY_NINETYNINE_DEVN: Final = ".99.devN"
POST_VERSION_STRATEGY_P1_DEVN: Final = "+1.devN"
POST_VERSION_STRATEGY_DOT_N: Final = ".N"


class MetadataOptions(TypedDict, total=False):
    depends_override: Optional[Dict[str, str]]
    external_dependencies_override: Optional[
        Dict[str, Dict[str, Union[str, List[str]]]]
    ]
    odoo_version_override: Optional[str]
    post_version_strategy_override: Optional[str]


def manifest_to_metadata(
    manifest: Manifest,
    options: Optional[MetadataOptions] = None,
    precomputed_metadata_path: Optional[Path] = None,
) -> Message:
    """Return Python Package Metadata 2.2 for an Odoo addon manifest as an
    ``email.message.Message``.

    The Description field is absent and is stored in the message payload.
    All values are guaranteed to not contain newline characters, except for
    the payload.

    ``precomputed_metadata_path`` may point to a file containing pre-computed
    metadata that will be used to obtain the Name and Version, instead of looking
    at the addon directory name or manifest version + VCS, respectively. This is useful
    to process a manifest from a sdist tarball with PKG-INFO, for example.
    """
    return _manifest_to_metadata_using_setuptools_odoo(
        manifest,
        options or MetadataOptions(),
        precomputed_metadata_path,
    )


def _manifest_to_metadata_using_setuptools_odoo(
    manifest: Manifest,
    options: MetadataOptions,
    precomputed_metadata_path: Optional[Path] = None,
) -> Message:
    from distutils.errors import DistutilsSetupError

    from setuptools_odoo import get_addon_metadata  # type: ignore

    try:
        return get_addon_metadata(  # type: ignore
            str(manifest.manifest_path.parent),
            depends_override=options.get("depends_override"),
            external_dependencies_override=options.get(
                "external_dependencies_override"
            ),
            odoo_version_override=options.get("odoo_version_override"),
            post_version_strategy_override=options.get(
                "post_version_strategy_override"
            ),
            precomputed_metadata_path=precomputed_metadata_path,
        )
    except DistutilsSetupError as e:
        if "Unsupported odoo version" in str(e):
            raise UnsupportedOdooVersion(str(e)) from e
        elif "Version in manifest must" in str(e):
            raise UnsupportedManifestVersion(str(e)) from e
        raise
