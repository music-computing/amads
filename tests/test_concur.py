from amads.time.concur import concur
from amads.core.basics import Score
from amads.io import partitura_midi_import
from amads.music import example
import numpy as np

def test_concur_type():
    s = Score.from_melody([60, 62, 64, 65])
    c = concur(s)
    assert type(c) == float and c == 0.0

