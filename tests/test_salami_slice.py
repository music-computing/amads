from pytest import approx

from amads.algorithms.slice.salami import Timepoint, salami_slice


def test_timepoints_twochan(twochan_notes):
    timepoints = Timepoint.from_notes(twochan_notes, time_n_digits=6)
    assert len([t for t in timepoints if len(t.note_ons) > 0]) == 16


def test_salami_slice_twochan(twochan_score):
    print("test_salami_slice_twochan(twochan_score): ")
    twochan_score.show()
    chords = salami_slice(twochan_score)
    print("after salami_slice:", chords)
    for chord in chords:
        print("chord at ", chord.onset)
        chord.show()
    assert len(chords) == 16

    pitches = [[int(p.num) for p in c.content] for c in chords]
    assert pitches == [
        [43, 67],
        [43, 64],
        [43, 67],
        [43, 65],
        [45, 67],
        [45, 64],
        [43, 67],
        [43, 71],
        [40, 69],
        [40, 71],
        [38, 74],
        [38, 71],
        [43, 69],
        [43, 67],
        [47, 64],
        [47, 67],
    ]

    for chord in chords:
        assert chord.duration == approx(1.0, abs=0.01)
