import runpy

import pytest

from amads.ci import should_run


@pytest.mark.parametrize(
    "demo_file",
    [
        "demos/melsim.py",
        "examples/plot_melsim.py",
    ],
)
def test_melsim_demos_run_without_errors(demo_file):
    """Test that melsim-related demo files run without errors."""
    if should_run(demo_file):
        runpy.run_path(demo_file, run_name="__main__")
