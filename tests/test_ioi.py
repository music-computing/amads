from amads.core.basics import Chord, Note, Part, Score


def test_ioi():
    """Test the ioi method of Note class."""
    # Create a simple melody with known IOIs
    score = Score.from_melody(
        pitches=[60, 62, 64],  # C4, D4, E4
        deltas=[0.0, 1.0, 3.0],  # Start times: 0, 1, 3
        durations=[0.5, 1.0, 1.0],  # Durations don't affect IOIs
    )

    notes = score.notes

    # First note has no previous note
    assert notes[0].ioi is None

    # Second note starts at 1.0, previous note at 0.0, so IOI = 1.0
    assert notes[1].ioi == 1.0

    # Third note starts at 3.0, previous note at 1.0, so IOI = 2.0
    assert notes[2].ioi == 2.0


def test_ioi_with_chords():
    """Test ioi with simultaneous notes (chords)."""
    score = Score()
    part = Part()
    score.insert(part)

    # Create a chord with three notes at t=0
    chord = Chord(duration=1.0, delta=0.0)
    for pitch in [60, 64, 67]:  # C4, E4, G4
        note = Note(duration=1.0, pitch=pitch)
        chord.insert(note)  # This sets the parent correctly
    part.insert(chord)  # This sets the parent correctly

    # Add a single note at t=2
    note = Note(duration=1.0, pitch=72, delta=2.0)  # C5
    part.insert(note)  # This sets the parent correctly

    notes = score.notes

    # First three notes have no previous onset time
    for i in range(3):
        assert notes[i].ioi is None

    # Last note starts at 2.0, previous notes at 0.0, so IOI = 2.0
    assert notes[3].ioi == 2.0


def test_ioi_ratio():
    """Test the ioi_ratio property of Note class."""
    # Create a melody with known IOIs
    score = Score.from_melody(
        pitches=[60, 62, 64, 65],  # C4, D4, E4, F4
        deltas=[0.0, 1.0, 3.0, 4.0],  # Start times: 0, 1, 3, 4
        durations=[0.5, 1.0, 0.5, 1.0],  # Durations don't affect IOIs
    )

    notes = score.notes

    # First note has no previous IOI
    assert notes[0].ioi_ratio is None

    # Second note has no previous IOI to compare with
    assert notes[1].ioi_ratio is None

    # Third note: current IOI = 2.0, previous IOI = 1.0, ratio = 2.0
    assert notes[2].ioi_ratio == 2.0

    # Fourth note: current IOI = 1.0, previous IOI = 2.0, ratio = 0.5
    assert notes[3].ioi_ratio == 0.5
