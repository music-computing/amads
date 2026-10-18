from pytest import approx

from amads.core.basics import Measure, Note, Part, Score, Staff, TimeSignature
from amads.core.timemap import MapQuarter
from amads.io.normalize import normalize


def _score(measure_lengths):
    score = Score()
    staff = Staff(parent=Part(parent=score))
    onset = 0
    for n in measure_lengths:
        m = Measure(parent=staff, onset=onset, duration=n)
        Note(parent=m, onset=onset, duration=n, pitch=60)
        onset += n
    return score


def _tempo_at_quarter(score, q):
    """qpm in effect just after quarter q."""
    return score.time_map.time_to_tempo(score.time_map.quarter_to_time(q))


def test_normalize_simple():
    score = _score([6, 4])
    score.time_map.changes = [MapQuarter(0, 0), MapQuarter(4, 6)]
    score.time_map.last_tempo = 1.0
    score.time_signatures = [TimeSignature(0, 4, 4), TimeSignature(6, 4, 4)]
    normalize(score)

    measures = list(score.find_all(Measure))
    assert [(m.onset, m.duration) for m in measures] == [(0, 4), (4, 4)]
    notes = list(score.find_all(Note))
    assert [(n.onset, n.duration) for n in notes] == [(0, 4), (4, 4)]
    assert score.time_signatures[1].quarters == approx(4)
    # 6 quarters in 4 s becomes 4 quarters in 4 * 4 / 6 s
    assert score.time_map.quarter_to_time(4) == approx(16 / 6)
    assert _tempo_at_quarter(score, 1) == approx(90)
    assert _tempo_at_quarter(score, 5) == approx(60)


def test_normalize_tempo_changes():
    # m1 (0-6) is over-long and has a tempo change at quarter 3;
    # m3 (10-14) starts with a tempo change.
    score = _score([6, 4, 4])
    score.time_map.changes = [
        MapQuarter(0, 0),
        MapQuarter(2, 3),
        MapQuarter(9, 10),
    ]
    score.time_map.last_tempo = 2.0  # 120 qpm
    normalize(score)

    measures = list(score.find_all(Measure))
    assert [m.onset for m in measures] == approx([0, 4, 8])
    assert all(m.duration == approx(4) for m in measures)

    tm = score.time_map
    # tempo change inside m1 moved proportionally: 3 -> 2
    assert any(c.quarter == approx(2) for c in tm.changes)
    assert _tempo_at_quarter(score, 1) == approx(90)
    assert _tempo_at_quarter(score, 3) == approx(60)
    assert _tempo_at_quarter(score, 7.9) == approx(60)
    # tempo change at the start of m3 is still at the start of m3
    m3 = measures[2]
    assert any(c.quarter == approx(m3.onset) for c in tm.changes)
    assert _tempo_at_quarter(score, m3.onset) == approx(120)
    # 5 s for 0-6 -> 5 * 4/6 s; then 7 quarters at 60 qpm up to quarter 10
    assert tm.quarter_to_time(m3.onset) == approx(9 - 5 / 3)
