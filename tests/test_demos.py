import runpy
from glob import glob

import pytest

from amads.ci import should_run


@pytest.mark.parametrize("file", glob("demos/*.py"))
def test_demos_run_without_errors(file):
    if file == "demos/durdist2.py":
        pytest.skip(
            "Skipping durdist2 demo (see https://github.com/music-computing/amads/issues/43)"
        )

    if should_run(file):
        runpy.run_path(file, run_name="__main__")
