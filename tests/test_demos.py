import runpy
from glob import glob
from pathlib import Path

import pytest

from conftest import should_run

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_FILES = sorted(glob(str(REPO_ROOT / "demos/*.py")))
RUNNABLE_DEMO_FILES = [
    file
    for file in DEMO_FILES
    if should_run(
        str(Path(file).resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    )
]


@pytest.mark.parametrize(
    "file",
    RUNNABLE_DEMO_FILES,
    ids=[Path(file).name for file in RUNNABLE_DEMO_FILES],
)
def test_demos_run_without_errors(file):
    runpy.run_path(file, run_name="__main__")
