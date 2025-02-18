Testing
=======

This project uses pytest for testing. To run the tests, follow these steps:

Prerequisites
------------

Make sure you have the development dependencies installed::

    pip install -e ".[dev]"

Running all tests
----------------

From the root directory of the project, run::

    pytest

Running specific tests
---------------------

To run tests in a specific file::

    pytest tests/test_pitch_list_transformations.py

To run a specific test function::

    pytest tests/test_pitch_list_transformations.py::test_function_name

Writing tests
------------

Tests are located in the ``tests/`` directory. Each test file should start with ``test_`` and each test function should also start with ``test_``.

Example test::

    def test_my_function():
        result = my_function()
        assert result == expected_value

Doctests
--------

The project also uses doctests for testing code examples in docstrings. Doctests are written in the docstring of a function and show example usage with expected outputs.
This is a great way to implement simple tests that also serve as useful documentation.

Example doctest::

    def entropy(d):
        """
        Calculate the relative entropy of a distribution.

        Parameters
        ----------
        d : list
            The input distribution.

        Returns
        -------
        float
            The relative entropy (0 <= H <= 1).

        Examples
        --------
        >>> entropy([0.5, 0.5])
        1.0
        """

These doctests are automatically run when you run ``pytest``.

Continuous Integration
----------------------

Tests are automatically run via GitHub Actions CI on pushes to main and pull requests.

You can view the CI configuration in ``.github/workflows/tests.yml``
and check test results in the "Actions" tab of the GitHub repository.

By default tests are run in the tests_main CI job.
However, some tests that require bespoke dependencies are run in separate CI jobs
(e.g. ``tests_melsim``).
