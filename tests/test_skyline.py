from amads.core.basics import Note, Part, Score
from amads.polyphony.skyline import extreme

# TODO test skyline and expand


def test_extreme():
    """
    Basic test of extreme 'high' and 'low' from dummy example.
    """
    score = Score()
    part = Part(parent=score)

    Note(parent=part, onset=0.0, duration=1.0, pitch=60)  # C4
    Note(parent=part, onset=0.0, duration=1.0, pitch=64)  # E4
    Note(parent=part, onset=0.0, duration=1.0, pitch=62)  # D4
    Note(parent=part, onset=1.0, duration=1.0, pitch=67)  # G4

    assert extreme(score, attribute="high") == 67
    assert extreme(score, attribute="low") == 60
