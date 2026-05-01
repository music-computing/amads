import importlib.util
import runpy
from glob import glob
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# Import repo-root conftest explicitly; ``tests/conftest.py`` would shadow ``from conftest``.
_spec = importlib.util.spec_from_file_location(
    "amads_root_conftest", REPO_ROOT / "conftest.py"
)
_root_conftest = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_root_conftest)
should_run = _root_conftest.should_run
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
