import sys

import pytest

coverage_args = ["--cov=./", "--cov-report=xml"]


def run_main_tests():
    """
    Run main tests with coverage.
    Tests are discovered following repo's pytest.ini file which says
    run tests in amads and tests named test_*, *_test, with classes
    Test* and function test_*.
    Assumes that the working directory is the root of the repository.
    """
    pytest_args = coverage_args
    sys.exit(pytest.main(pytest_args))
