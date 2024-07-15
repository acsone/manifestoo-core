import os
import subprocess
import sys
from pathlib import Path
from typing import Iterator, List, Optional, TextIO

from packaging.version import parse as parse_version

if sys.version_info >= (3, 8):
    from typing import Final
else:
    from typing_extensions import Final

from .addon import Addon
from .exceptions import InvalidManifest, UnknownPostVersionStrategy
from .manifest import MANIFEST_NAMES, Manifest

POST_VERSION_STRATEGY_NONE: Final = "none"
POST_VERSION_STRATEGY_NINETYNINE_DEVN: Final = ".99.devN"
POST_VERSION_STRATEGY_P1_DEVN: Final = "+1.devN"
POST_VERSION_STRATEGY_DOT_N: Final = ".N"


def _run_git_command_exit_code(
    args: List[str],
    cwd: Optional[Path] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    return subprocess.call(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=cwd,
        stderr=stderr,
    )


def _run_git_command_bytes(
    args: List[str],
    cwd: Optional[Path] = None,
    stderr: Optional[TextIO] = None,
) -> str:
    output = subprocess.check_output(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=cwd,
        universal_newlines=True,
        stderr=stderr,
    )
    return output.strip()


def _run_git_command_lines(
    args: List[str],
    cwd: Optional[Path] = None,
    stderr: Optional[TextIO] = None,
) -> List[str]:
    output = _run_git_command_bytes(args, cwd=cwd, stderr=stderr)
    return output.split("\n")


def _is_git_controlled(path: Path) -> bool:
    with Path(os.devnull).open("w") as devnull:
        r = _run_git_command_exit_code(["rev-parse"], cwd=path, stderr=devnull)
        return r == 0


def _get_git_uncommitted(path: Path) -> bool:
    r = _run_git_command_exit_code(["diff", "--quiet", "--exit-code", "."], cwd=path)
    return r != 0


def _get_git_root(path: Path) -> Path:
    return Path(_run_git_command_bytes(["rev-parse", "--show-toplevel"], cwd=path))


def _git_log_iterator(path: Path) -> Iterator[str]:
    """yield commits using git log -- <dir>"""
    n = 10
    count = 0
    while True:
        lines = _run_git_command_lines(
            ["log", "--oneline", "-n", str(n), "--skip", str(count), "--", "."],
            cwd=path,
        )
        for line in lines:
            sha = line.split(" ", 1)[0]
            count += 1
            yield sha
        if len(lines) < n:
            break


def _read_manifest_from_sha(
    sha: str,
    addon_dir: Path,
    git_root: Path,
) -> Optional[Manifest]:
    rel_addon_dir = addon_dir.relative_to(git_root)
    for manifest_name in MANIFEST_NAMES:
        manifest_path = rel_addon_dir / manifest_name
        try:
            with Path(os.devnull).open("w") as devnull:
                s = _run_git_command_bytes(
                    ["show", f"{sha}:{manifest_path}"],
                    cwd=git_root,
                    stderr=devnull,
                )
        except subprocess.CalledProcessError:
            continue
        try:
            return Manifest.from_str(s)
        except InvalidManifest:
            break
    return None


def _bump_last(version: str) -> str:
    int_version = [int(i) for i in version.split(".")]
    int_version[-1] += 1
    return ".".join(str(i) for i in int_version)


def get_git_postversion(  # noqa: C901, PLR0911, PLR0912 too complex
    addon: Addon,
    strategy: str,
) -> str:
    """return the addon version number, with a developmental version increment
    if there were git commits in the addon_dir after the last version change.

    If the last change to the addon correspond to the version number in the
    manifest it is used as is for the python package version. Otherwise a
    counter is incremented for each commit and resulting version number has
    the following form, depending on the strategy (N being the number of git
    commits since the version change):

    * STRATEGY_NONE: return the version in the manifest as is
    * STRATEGY_99_DEVN: [8|9].0.x.y.z.99.devN
    * STRATEGY_P1_DEVN: [series].0.x.y.(z+1).devN
    * STRATEGY_DOT_N: [series].0.x.y.z.N

    Notes:

    * pip ignores .postN  by design (https://github.com/pypa/pip/issues/2872)
    * x.y.z.devN is anterior to x.y.z

    Note: we don't put the sha1 of the commit in the version number because
    this is not PEP 440 compliant and is therefore misinterpreted by pip.
    """
    last_version = addon.manifest.version or "0.0.0"
    addon_dir = addon.path.resolve()
    if strategy == POST_VERSION_STRATEGY_NONE:
        return last_version
    last_version_parsed = parse_version(last_version)
    if not _is_git_controlled(addon_dir):
        return last_version
    if _get_git_uncommitted(addon_dir):
        uncommitted = True
        count = 1
    else:
        uncommitted = False
        count = 0
    last_sha = None
    git_root = _get_git_root(addon_dir)
    for sha in _git_log_iterator(addon_dir):
        manifest = _read_manifest_from_sha(sha, addon_dir, git_root)
        if manifest is None:
            break
        version = manifest.version or "0.0.0"
        version_parsed = parse_version(version)
        if version_parsed != last_version_parsed:
            break
        if last_sha is None:
            last_sha = sha
        else:
            count += 1
    if not count:
        return last_version
    if last_sha:
        if strategy == POST_VERSION_STRATEGY_NINETYNINE_DEVN:
            return last_version + f".99.dev{count}"
        if strategy == POST_VERSION_STRATEGY_P1_DEVN:
            return _bump_last(last_version) + f".dev{count}"
        if strategy == POST_VERSION_STRATEGY_DOT_N:
            return last_version + f".{count}"
        msg = f"Unknown postversion strategy: {strategy}"
        raise UnknownPostVersionStrategy(msg)
    if uncommitted:
        return last_version + ".dev1"
    # if everything is committed, the last commit
    # must have the same version as current,
    # so last_sha must be set and we'll never reach this branch
    return last_version
