"""Test partimenti module.

This module tests the partimenti module functionality.

Created by Mark Gotham, 2019.

License: Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/
"""

import pytest

from amads.schemata.partimenti import *


@pytest.mark.parametrize("partimento", [
    aprile,
    cadenza_doppia,
    cadenza_semplice,
    comma,
    converging,
    deceptive,
    do_re_mi,
    evaded,
    fonte,
    fenaroli,
    indugio,
    jupiter,
    meyer,
    modulating_prinner,
    monte,
    passo_indietro,
    pastorella,
    ponte,
    prinner,
    quiescenza,
    romanesca,
    sol_fa_mi
], ids=lambda x: x["name"])  # Use the partimento name as the test ID
def test_partimenti_length(partimento):
    """Test that partimento sections have consistent lengths.

    Each partimento should have melody, bass, and figures sections
    of equal length.
    """
    assert len(partimento["melody"]) == len(partimento["bass"])
    assert len(partimento["melody"]) == len(partimento["figures"])


# TODO: fix the following errors:
# FAILED tests_to_fix/test_partimenti.py::test_partimenti_length[Modulating Prinner] - AssertionError: assert 4 == 5
# FAILED tests_to_fix/test_partimenti.py::test_partimenti_length[Monte] - AssertionError: assert 6 == 4
# FAILED tests_to_fix/test_partimenti.py::test_partimenti_length[Prinner] - assert 4 == 5
