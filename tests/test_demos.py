import runpy
from glob import glob
from pathlib import Path

import pytest

from amads.ci import should_run


@pytest.mark.parametrize(
    "file", glob(str(Path(__file__).parent.parent / "demos/*.py"))
)
def test_demos_run_without_errors(file):
    if should_run(file):
        runpy.run_path(file, run_name="__main__")
