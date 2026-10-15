# example.py -- access to music examples
#
# Roger B. Dannenberg
# Sep 2024

import os
from importlib import resources, util

from amads.io.readscore import valid_score_extensions


def fullpath(example: str) -> str:
    """Construct a full path name for an example file.

    For example, fullpath("midi/sarabande.mid") returns a path to a
    readable file from this package.  This uses importlib so that
    we can read files even from compressed packages (we hope).

    Parameters
    ----------
    example : str
        The relative path to the example file, starting from the "music"
        directory. For example, "midi/sarabande.mid" or "musicxml/ex2.xml".

    Returns
    -------
    str
        The full path to the example file.

    Raises
    ------
    FileNotFoundError
        If the example file is not found or is not readable.
    """

    def trim_path(full: str) -> str:
        """remove first part of path to construct valid parameter value"""
        first_part = "amads/music/"
        index = full.find(first_part)
        return full if index == -1 else full[index + len(first_part) :]

    path = str(resources.files("amads").joinpath("music/" + example))

    if os.path.isfile(path) and os.access(path, os.R_OK):
        return path

    print("In amads.example.fullpath(" + example + "):")
    print("    File was not found. Try one of these:")

    spec = util.find_spec("amads")
    if spec is None:
        print("Error: Package amads not found")
        raise FileNotFoundError("Package amads not found")
    if spec.submodule_search_locations is None:
        print("Error: Package amads has no submodule search locations")
        raise FileNotFoundError(
            "Package amads has no submodule search locations"
        )
    package_path = spec.submodule_search_locations[0]

    # Walk through the directory hierarchy
    for root, dirs, files in os.walk(package_path):
        for file in files:
            for ext in valid_score_extensions:
                if file.endswith(ext):
                    parameter_option = trim_path(os.path.join(root, file))
                    print(f'   "{parameter_option}"')
    raise FileNotFoundError("Example file not found")
