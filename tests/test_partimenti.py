"""Test partimenti module.

This module tests the partimenti module functionality.

Created by Mark Gotham, 2019.

License: Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/
"""

__author__ = "Mark Gotham"


# ------------------------------------------------------------------------------

from amads.schema.partimenti import all


def test_partimenti_length():
    """Test that partimento sections have consistent lengths ("stages").

    Each partimento should have melody, bass, and figures sections
    of equal length.
    """
    for p in all:
        assert len(p["melody"]) == len(p["bass"])
        assert len(p["melody"]) == len(p["figures"])
