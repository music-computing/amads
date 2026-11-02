"""
Tests for amads/time/onsetacorr.py
"""

import pytest

from amads.io.pm_midi_import import pretty_midi_import
from amads.music import example

from amads.time.onsetacorr import *
from amads.io.readscore import read_score

from tests.matlab_crosstesting_utils import load_json_results

def test_autocorr_sarabande():
    score = pretty_midi_import(
        example.fullpath("midi/sarabande.mid"), "midi", flatten=True
    )

    ac = onset_autocorr(score)

    json_data = load_json_results()
    # This desired data result is obtained from matlab testing
    expected = json_data["onset_autocorr"]

    assert ac == pytest.approx(expected, abs=1e-6)