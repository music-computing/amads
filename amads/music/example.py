# example.py -- access to music examples
#
# Roger B. Dannenberg
# Sep 2024

import os
from importlib import resources, util

music_extensions = [".mid", ".xml"]  # used to find all music examples


def fullpath(example):
    """Construct a full path name for an example file.
    For example, fullpath("midi/sarabande.mid") returns a path to a
    readable file from this package.  This uses importlib so that
    we can read files even from compressed packages (we hope).
    """

    def trim_path(full):
        """remove first part of path to construct valid parameter value"""
        index = full.find("amads/music")
        return full if index == -1 else full[index + 14 :]

    path = resources.files("amads").joinpath("music/" + example)

    if os.path.isfile(path) and os.access(path, os.R_OK):
        return path

    print("In amads.example.fullpath(" + example + "):")
    print("    File was not found. Try one of these:")

    spec = util.find_spec("amads")
    if spec is None:
        print("Error: Package amads not found")
        return None

    package_path = spec.submodule_search_locations[0]

    # Walk through the directory hierarchy
    for root, dirs, files in os.walk(package_path):
        for file in files:
            for ext in music_extensions:
                if file.endswith(ext):
                    parameter_option = trim_path(os.path.join(root, file))
                    print(f'   "{parameter_option}"')
    return None
