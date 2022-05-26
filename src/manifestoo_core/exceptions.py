class ManifestooException(Exception):
    """Base class of all manifestoo_core exceptions."""


class UnsupportedOdooVersion(ManifestooException):
    pass


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
