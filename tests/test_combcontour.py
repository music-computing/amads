from amads.melody.contour.combcontour import combcontour
from amads.core.basics import Score
from amads.io import partitura_midi_import
from amads.music import example
import numpy as np

def test_combcontour_type():
    s = Score.from_melody([60, 62, 64, 65])
    assert type(combcontour(s)) == np.ndarray

def test_combcontour_basic():
    s = Score.from_melody([60, 62, 64, 65])
    assert np.array_equal(combcontour(s), [[0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0]])

def test_combcontour_more():
    s = Score.from_melody([7, 68, 20, 36, 110, 60, 79, 42])
    assert np.array_equal(combcontour(s), [[0,0,0,0,0,0,0,0],
                                           [1,0,1,1,0,1,0,1],
                                           [1,0,0,0,0,0,0,0],
                                           [1,0,1,0,0,0,0,0],
                                           [1,1,1,1,0,1,1,1],
                                           [1,0,1,1,0,0,0,1],
                                           [1,1,1,1,0,1,0,1],
                                           [1,0,1,1,0,0,0,0]])
    
def test_combcontour_polyphonic():
    my_midi_file = example.fullpath("midi/wtcii01a.mid")
    s = partitura_midi_import(my_midi_file)
    c = combcontour(s)
    assert c == None
    

    
