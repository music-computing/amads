import runpy
from glob import glob

import pytest

from amads.ci import should_run


@pytest.mark.parametrize("file", glob("demos/*.py"))
def test_demos_run_without_errors(file):
    if should_run(file):
        runpy.run_path(file, run_name="__main__")
