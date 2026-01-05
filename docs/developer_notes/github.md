# Github

This page describes configuration details for Github.

See also [GitHub contribution workflow](../contributing/#github-contribution-workflow).

## Testing and Continuous Integration

The configuration is in `.github/workflows/tests.yml`

There are two (potential) sets of tests:

    python -c "from amads.ci import run_main_tests; run_main_tests()"
    
which is actually run, and the following which is commented out:

    python -c "from amads.ci import run_ci_group_tests;
    run_ci_group_tests('tests_melsim')"
    
We had problems with melsim, probably related to its dependency on R.

::: amads.ci.run_main_tests




