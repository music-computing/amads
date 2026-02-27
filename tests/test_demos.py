import runpy
from glob import glob
from pathlib import Path

import pytest

from amads.ci import should_run


@pytest.mark.parametrize(
    "file", glob(str(Path(__file__).parent.parent / "demos/*.py"))
)
def test_demos_run_without_errors(file):
    # parent of __file__ is tests, so parent.parent is repo root:
    repo_root = Path(__file__).resolve().parent.parent
    relative_file = str(Path(file).resolve().relative_to(repo_root)).replace(
        "\\", "/"
    )
    if should_run(relative_file):
        runpy.run_path(file, run_name="__main__")
