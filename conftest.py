# This tells pytest not to try and collect tests from demos, docs, examples, or tests_to_fix.
# Note that the demos are tested separately in tests/test_demos.py.
collect_ignore = ["demos", "docs", "examples", "tests_to_fix", "amads/all.py"]


# suggested by GPT, but this seems to be specific to one machine so
# it is not appropriate to put this in conftest.py
#
# import os
# from pathlib import Path
#
# def pytest_sessionstart(session):
#     homebrew_bin = "/opt/homebrew/bin"
#     if not Path(homebrew_bin).is_dir():
#         return
#
#     path = os.environ.get("PATH", "")
#     parts = path.split(os.pathsep) if path else []
#     if homebrew_bin not in parts:
#         os.environ["PATH"] = (
#             f"{homebrew_bin}{os.pathsep}{path}" if path else homebrew_bin
#         )
