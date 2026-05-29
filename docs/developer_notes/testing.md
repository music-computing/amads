# Testing

This project uses pytest for testing. To run the tests, follow these
steps:

## Prerequisites

Make sure you have the development dependencies installed:

    pip install -e ".[dev]"

## Running all tests

From the root directory of the project, run:

    pytest

### Running specific tests

To run tests in a specific file:

    pytest tests/test_pitch_list_transformations.py

To run a specific test function:

    pytest
    tests/test_pitch_list_transformations.py::test_function_name

## Code Coverage 

To measure how much code is covered by tests 

 - Install `coverage`, e.g., `pip3 install coverage`
 - Install `pytest-cov`, e.g., `pip3 install pytest-cov`
 - Current directory should be the repo root ABOVE amads, 
   e.g., current directory should contain amads, tests, and demos 
 - Run `coverage run -m pytest`
 - View results with `coverage report` or `coverage html`

## Testing with VSCode

Install pytest-cov:

    pip install pytest-cov

Install anyio:

    pip install anyio

In VSCode, type Command Shift P and from the (large) command menu, find
“Python: Configure Tests”. Select “pytest” and then “. (Root
directory)”. Then all tests appear in the Test Explorer.

To get to Test Explorer, select the Erlenmeyer (conical) flask icon in
the far left column (pop-up description is “Testing”.

Select a test or set of tests. In the selected test, there are small
icons to run, run with debugger, or run with coverage, so pick one.

## Writing tests

Tests are located in the `tests/` directory. Each test file should start
with `test_` and each test function should also start with `test_`.

Example test:

    def test_my_function():
        result = my_function()
        assert result == expected_value

## Doctests

The project also uses doctests for testing code examples in docstrings.
Doctests are written in the docstring of a function and show example
usage with expected outputs. This is a great way to implement simple
tests that also serve as useful documentation.

Example doctest:

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

        >>> entropy(         # multiple line example
        ...     [0.5, 0.5]
        ... )
        1.0
        """

These doctests are automatically run when you run `pytest`.

## Continuous Integration

Tests are automatically run via GitHub Actions CI on pushes to main and
pull requests.

You can view the CI configuration in `.github/workflows/tests.yml` and
check test results in the “Actions” tab of the GitHub repository.

By default tests are run in the `tests_main` CI job.

Test selection logic (what is skipped because optional dependencies are
missing) is centralized in `conftest.py`. This means that *local `pytest`
runs and CI runs use the same selection logic.*


The current dependency-aware selection includes paths that require R
(`melsim`) and paths that require `lilypond`.

`tests/test_demos.py` merely tests that every demo runs without error.
*Some* demos need to be disabled when dependencies are unavailable,
so `tests/test_demos.py` uses `should_run(...)` from `conftest.py` to skip
individual demos when their dependencies are unavailable.

## Troubleshooting optional dependencies

A drawback of the current system is *there is no warning if tests are
skipped* due to failure to find dependencies like R and lilypond. For
complete testing, you should check, e.g., that 
`test_demos/test_demos_run_without_errors[display_demo.py]` runs
(depends on lilypond) and
`test_demos/test_demos_run_without_errors[melsim.py]` runs (depends on
R).

If some tests are skipped unexpectedly, verify optional dependencies
(at present these are R and lilypond) in your shell environment:

Check `lilypond`:

    lilypond --version

If this command fails, install `lilypond` and make sure it is on your
`PATH`.

Check R availability for `melsim` tests:

    R --version

Then verify the Python-side R dependencies used by `melsim`:

    python -c "from amads.melody.similarity.melsim import check_r_packages_installed; print(check_r_packages_installed())"

If this prints `False` or raises an error, install the required R
packages.

Once you have dependencies (R and lilypond), run `pytest` command
in the AMADS root directory and see if all tests run.

When tests are running in a shell, you can try them with VS Code.
If VS Code fails to run tests that are run from `pytest` in a shell,
then there is a VS Code configuration problem.
On macOS (Apple Silicon), Homebrew tools are typically installed under
`/opt/homebrew/bin`. My (RBD) `.vscode/launch.json` file looks like
this (notice "env" includes `/opt/homebrew/bin`):
```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug current Python file",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PATH": "/opt/homebrew/bin:${env:PATH}",
                "PYTHONUNBUFFERED": "1"
            }
        },
        {
            "name": "Debug pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": [
                "${file}",
                "-s",
                "-v",
                "--capture=no"
            ],
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PATH": "/opt/homebrew/bin:${env:PATH}",
                "PYTHONUNBUFFERED": "1"
            }
        }
    ]
}
```


## Graphical Display and Testing

Demos (and maybe examples) are "tested" by running them. This can
annoying when demos open programs or create plots that the user
must manually close every time the tests are run.

To suppress graphical output during testing, there are two mechanisms:

- With matplotlib (all plots and pianroll display), it seems that
  when the test completes, the job is terminated and the display
  is removed, possibly before a window can even be opened. (If this
  stops working, using `AMADS_NO_OPEN`, described next, would be a
  good mechanism to build on.)
- Music display via PDF or MuseScore (application) is suppressed
  when the shell environment variable `AMADS_NO_OPEN` is "1". The
  display code checks for this, and there are hooks so that
  `AMADS_NO_OPEN` is set to "1" for the duration of a `pytest` run.
