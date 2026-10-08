import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

import pytest

from manifestoo_core.addon import Addon
from manifestoo_core.git_postversion import (
    POST_VERSION_STRATEGY_DOT_N,
    POST_VERSION_STRATEGY_NINETYNINE_DEVN,
    POST_VERSION_STRATEGY_NONE,
    POST_VERSION_STRATEGY_P1_DEVN,
    get_git_postversion,
)


class Repo:
    """A git repository with one addon, with controlled commit dates."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.addon_dir = path / "addon1"
        self.addon_dir.mkdir()
        (self.addon_dir / "__init__.py").touch()
        self._time = 1_700_000_000
        self.git("init", "--initial-branch=main")

    def git(self, *args: str, date: Optional[int] = None) -> str:
        env: Dict[str, str] = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        if date is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{date} +0000"
        return subprocess.check_output(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=self.path,
            env=env,
            universal_newlines=True,
        ).strip()

    def commit(
        self,
        version: Optional[str] = None,
        filename: str = "file.py",
        date: Optional[int] = None,
    ) -> str:
        if date is None:
            self._time += 60
            date = self._time
        if version is not None:
            (self.addon_dir / "__manifest__.py").write_text(
                repr({"name": "addon1", "version": version})
            )
        with (self.addon_dir / filename).open("a") as f:
            f.write(f"# {date}\n")
        self.git("add", ".")
        self.git("commit", "-m", f"commit at {date}", date=date)
        return self.git("rev-parse", "HEAD")

    def postversion(self, strategy: str = POST_VERSION_STRATEGY_P1_DEVN) -> str:
        return get_git_postversion(Addon.from_addon_dir(self.addon_dir), strategy)


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path)


def test_not_git(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addon1"
    addon_dir.mkdir()
    (addon_dir / "__init__.py").touch()
    (addon_dir / "__manifest__.py").write_text("{'version': '16.0.1.0.0'}")
    addon = Addon.from_addon_dir(addon_dir)
    assert get_git_postversion(addon, POST_VERSION_STRATEGY_P1_DEVN) == "16.0.1.0.0"


def test_version_commit(repo: Repo) -> None:
    repo.commit(version="16.0.1.0.0")
    assert repo.postversion() == "16.0.1.0.0"


@pytest.mark.parametrize(
    ("strategy", "expected"),
    [
        (POST_VERSION_STRATEGY_NONE, "16.0.1.0.0"),
        (POST_VERSION_STRATEGY_P1_DEVN, "16.0.1.0.1.dev2"),
        (POST_VERSION_STRATEGY_NINETYNINE_DEVN, "16.0.1.0.0.99.dev2"),
        (POST_VERSION_STRATEGY_DOT_N, "16.0.1.0.0.2"),
    ],
)
def test_linear_history(repo: Repo, strategy: str, expected: str) -> None:
    repo.commit(version="15.0.1.0.0")
    repo.commit(version="16.0.1.0.0")
    repo.commit()
    repo.commit()
    assert repo.postversion(strategy) == expected


def test_uncommitted(repo: Repo) -> None:
    repo.commit(version="16.0.1.0.0")
    (repo.addon_dir / "file.py").write_text("changed\n")
    assert repo.postversion() == "16.0.1.0.1.dev1"
    repo.commit()
    (repo.addon_dir / "file.py").write_text("changed again\n")
    assert repo.postversion() == "16.0.1.0.1.dev2"


def test_uncommitted_version_change(repo: Repo) -> None:
    repo.commit(version="16.0.1.0.0")
    (repo.addon_dir / "__manifest__.py").write_text(
        "{'name': 'addon1', 'version': '16.0.1.0.1'}"
    )
    assert repo.postversion() == "16.0.1.0.1.dev1"


def test_merge_commit(repo: Repo) -> None:
    """A merged branch created before the version bump does not stop the count.

    The branch commit is newer than the version bump, so git log lists it
    between the merge commit and the version bump, with the old version in
    its manifest.
    """
    base = repo.commit(version="16.0.1.0.0", date=1_700_000_000)
    repo.commit(version="16.0.1.0.1", date=1_700_000_100)  # version bump
    repo.git("checkout", "-b", "feature", base)
    repo.commit(filename="feature.py", date=1_700_000_200)
    repo.git("checkout", "main")
    repo.commit(date=1_700_000_300)
    repo.git("merge", "--no-ff", "-m", "merge feature", "feature", date=1_700_000_400)
    # merge commit, main commit and feature commit since the version bump
    assert repo.postversion() == "16.0.1.0.2.dev3"
    # the version keeps increasing with new commits
    repo.commit(date=1_700_000_500)
    assert repo.postversion() == "16.0.1.0.2.dev4"


def test_merge_commit_after_bump(repo: Repo) -> None:
    """Version bump right after a merge, as done by the OCA bot."""
    base = repo.commit(version="16.0.1.0.0", date=1_700_000_000)
    repo.git("checkout", "-b", "feature", base)
    repo.commit(filename="feature.py", date=1_700_000_100)
    repo.git("checkout", "main")
    repo.git("merge", "--no-ff", "-m", "merge feature", "feature", date=1_700_000_200)
    repo.commit(version="16.0.1.0.1", date=1_700_000_300)  # post-merge bump
    assert repo.postversion() == "16.0.1.0.1"
    repo.commit(date=1_700_000_400)
    assert repo.postversion() == "16.0.1.0.2.dev1"
