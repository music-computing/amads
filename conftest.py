import os
import subprocess
from pathlib import Path

from amads.melody.similarity.melsim import check_r_packages_installed

# This tells pytest not to try and collect tests from demos, docs, examples, or tests_to_fix.
# Note that the demos are tested separately in tests/test_demos.py.
_ignore_tests = ["demos", "docs", "examples", "tests_to_fix", "amads/all.py"]

# test paths that depend upon R installation
_melsim_test_paths = [
    "tests/test_melsim.py",
    "tests/test_melsim_demos.py",
    "amads/melody/similarity/melsim.py",
    "examples/plot_melsim.py",
    "demos/melsim.py",
]

# test paths that depend upon lilypond installation
_lilypond_test_paths = [
    "demos/display_demo.py",  # depends on lilypond and opens PDF file
]


def _normalize_path(path):
    return str(path).replace("\\", "/").removeprefix("./")


def _lilypond_available():
    try:
        result = subprocess.run(
            ["lilypond", "--version"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


try:
    check_r_packages_installed()
except Exception:
    _ignore_tests.extend(_melsim_test_paths)

if not _lilypond_available():
    _ignore_tests.extend(_lilypond_test_paths)


_REPO_ROOT = Path(__file__).resolve().parent
_IGNORED_PATHS = {_normalize_path(path) for path in _ignore_tests}


def should_run(path):
    """Determine if a test path should be run based on available dependencies."""
    return _normalize_path(path) not in _IGNORED_PATHS


def pytest_ignore_collect(collection_path, config):
    """Skip collecting files/directories listed in _ignore_tests."""
    try:
        relative_path = _normalize_path(
            Path(collection_path).resolve().relative_to(_REPO_ROOT)
        )
    except ValueError:
        return False

    for ignored_path in _IGNORED_PATHS:
        if (
            relative_path == ignored_path
            or relative_path.startswith(f"{ignored_path}/")
        ):
            return True
    return False


def pytest_sessionstart(session):
    os.environ["AMADS_NO_OPEN"] = "1"


def pytest_sessionfinish(session, exitstatus):
    os.environ.pop("AMADS_NO_OPEN", None)
