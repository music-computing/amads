import os
import sys

import pytest

# This dictionary specifies tests that are not run in the default tests_main CI job.
# The keys are the names of the CI jobs that they should be tested in,
# and the values are lists of paths to test.
ci_groups = {
    "tests_melsim": [
        "tests/test_melsim.py",
        "amads/melody/similarity/melsim.py",
        "examples/plot_melsim.py",
    ]
}

paths_in_ci_groups = [path for paths in ci_groups.values() for path in paths]
coverage_args = ["--cov=./", "--cov-report=xml"]


def run_main_tests():
    """
    Run the main tests, i.e. all tests except those in the ci_groups dictionary.
    Assumes that the working directory is the root of the repository.
    """
    paths_to_ignore = paths_in_ci_groups
    ignore_args = [f"--ignore={path}" for path in paths_to_ignore]
    pytest_args = coverage_args + ignore_args
    sys.exit(pytest.main(pytest_args))


def run_ci_group_tests(job_name):
    """
    Run the tests for a specific CI job.
    Assumes that the working directory is the root of the repository.
    """
    paths_to_test = ci_groups[job_name]
    pytest_args = coverage_args + paths_to_test
    sys.exit(pytest.main(pytest_args))


def should_run(path):
    """Determine if a test should be run based on the CI environment."""
    if not os.environ.get("CI"):
        return True

    job = os.environ.get("GITHUB_JOB")
    if not job:
        raise ValueError("GITHUB_JOB environment variable not set")

    if job == "tests_main":
        return path not in paths_in_ci_groups

    return path in ci_groups[job]
