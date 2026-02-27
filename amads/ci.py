import subprocess
import sys

import pytest

from amads.melody.similarity.melsim import check_r_packages_installed

ci_ignore_paths = []

# test paths that depend upon R installation
melsim_test_paths = [
    "tests/test_melsim.py",
    "tests/test_melsim_demos.py",
    "amads/melody/similarity/melsim.py",
    "examples/plot_melsim.py",
    "demos/melsim.py",
]

# test paths that depend upon lilypond installation
lilypond_test_paths = [
    "demos/display_demo.py",  # depends on lilypond and opens PDF file
]

coverage_args = ["--cov=./", "--cov-report=xml"]

# Is R installed for melsim?
try:
    if check_r_packages_installed():
        pass
except Exception:
    ci_ignore_paths = ci_ignore_paths + melsim_test_paths

# Is lilypond installed?
result = subprocess.run(["lilypond"], capture_output=True, text=True)
if result.returncode != 0:
    ci_ignore_paths = ci_ignore_paths + lilypond_test_paths


def run_main_tests():
    """
    Run the main tests, i.e. all tests except those in ci_ignore_paths.
    Tests are discovered following repo's pytest.ini file which says
    run tests in amads and tests named test_*, *_test, with classes
    Test* and function test_*.
    Assumes that the working directory is the root of the repository.
    """
    ignore_args = [f"--ignore={path}" for path in ci_ignore_paths]
    pytest_args = coverage_args + ignore_args
    sys.exit(pytest.main(pytest_args))


def should_run(path):
    """Determine if a test should be run. This is used to deselect
    demos and examples which are all run in a single test (test_demos.py
    and test_examples.py) so they use this function to exclude certain
    demos and examples that do not have the necessary dependencies to run.
    """
    return path not in ci_ignore_paths
