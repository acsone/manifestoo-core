class ManifestooException(Exception):  # noqa: N818
    """Base class of all manifestoo_core exceptions."""


class UnsupportedOdooSeries(ManifestooException):
    pass


# compatibility alias
UnsupportedOdooVersion = UnsupportedOdooSeries


class UnsupportedManifestVersion(ManifestooException):
    pass


class InvalidManifest(ManifestooException):
    pass


class AddonNotFound(ManifestooException):
    pass


class AddonNotFoundNotInstallable(AddonNotFound):
    pass


class AddonNotFoundNoInit(AddonNotFound):
    pass


class AddonNotFoundNoManifest(AddonNotFound):
    pass


class AddonNotFoundNotADirectory(AddonNotFound):
    pass


class AddonNotFoundInvalidManifest(AddonNotFound):
    pass


class InvalidDistributionName(ManifestooException):
    pass


class UnknownPostVersionStrategy(ManifestooException):
    pass
