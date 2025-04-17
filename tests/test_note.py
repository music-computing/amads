from amads.core.basics import Note


def test_ties():
    note_1 = Note(onset=0.0, duration=1.0, pitch=60)
    note_2 = Note(onset=1.0, duration=1.0, pitch=60)

    note_1.tie = note_2

    # I'm not sure if this is the desired behavior,
    # but it's what the code looks like it's trying to do
    assert note_1.duration == 1.0
    assert note_1.tied_duration == 2.0
