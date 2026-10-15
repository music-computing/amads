"""
Normalize measure durations of a Score to match their time signatures.

<small>**Author**: Roger Dannenberg</small>
"""

from bisect import bisect_right
from typing import List

from amads.core.basics import Event, EventGroup, Measure, Score
from amads.core.timemap import MapQuarter

_TOLERANCE = 0.002  # quarters


class _Adjustment:
    """One shortened measure, in original coordinates."""

    __slots__ = [
        "start",
        "end",
        "ratio",
        "tstart",
        "tend",
        "q_before",
        "t_before",
    ]

    def __init__(self, start, end, new_len, tstart, tend):
        self.start = start
        self.end = end
        self.ratio = new_len / (end - start)
        self.tstart = tstart  # original seconds at start and end
        self.tend = tend
        self.q_before = 0.0  # quarters removed by earlier adjustments
        self.t_before = 0.0  # seconds removed by earlier adjustments


def _find_adjustments(score: Score) -> List[_Adjustment]:
    by_start = {}
    for m in score.find_all(Measure):
        ts = m.time_signature()
        if ts is None:
            continue
        nominal = ts.duration
        if m.duration > nominal + _TOLERANCE:
            by_start.setdefault(round(m.onset, 3), (m.onset, m.offset, nominal))
    tm = score.time_map
    adjustments = []
    q_removed = t_removed = 0.0
    for start, end, nominal in (by_start[k] for k in sorted(by_start)):
        if adjustments and start < adjustments[-1].end - _TOLERANCE:
            continue  # overlapping measure from another part; ignore
        adj = _Adjustment(
            start,
            end,
            nominal,
            tm.quarter_to_time(start),
            tm.quarter_to_time(end),
        )
        adj.q_before = q_removed
        adj.t_before = t_removed
        q_removed += (end - start) - nominal
        t_removed += (adj.tend - adj.tstart) * (1 - adj.ratio)
        adjustments.append(adj)
    return adjustments


def normalize(score: Score) -> Score:
    """Rescale measures that are longer than their time signature.

    Some scores have measures with extra duration, perhaps from
    cadenza-like runs of thirty-second notes that exceed the expected
    measure length according to strict interpretation and the time
    signature. Normally, this results in a score where the measure
    duration is extended beyond the duration implied by the time
    signature, and notes all receive their full duration according
    to the tempo.

    An alternative interpretation is to "squeeze" the notes into the
    number of quarters indicated by the time signature, resulting in
    faster performance of the notes within the measure, not by changing
    the tempo, but by changing their onset times and durations. For
    example, this could result in 37 "32nd" notes in the time of 4
    quarters. I.e., original 32nd notes are converted to 37th notes.

    This `normalize` function achieves this result for all measures
    that are longer than indicated by the time signature. Too-short
    measures are *not* "expanded" since they often occur correctly as
    pick-up measures, shortened first-ending measures, or final measures.

    Function behavior: Each measure whose duration exceeds the nominal
    duration given by its time signature is linearly compressed, in both
    onset times and durations of its content, to the nominal
    duration. Everything after a compressed measure is shifted earlier,
    including time signature positions and time map breakpoints. Tempo
    is preserved, so the time map is compressed in seconds by the same
    ratio as in quarters.  Measures that are shorter than nominal
    (e.g. pickup measures) are not changed.

    The score is modified in place in a single pass over its content,
    time signatures and time map.

    Parameters
    ----------
    score : Score
        The score to normalize.

    Returns
    -------
    Score
        The same score object, modified.
    """
    was_seconds = score.units_are_seconds
    if was_seconds:
        score.convert_to_quarters()

    adjustments = _find_adjustments(score)
    if not adjustments:
        if was_seconds:
            score.convert_to_seconds()
        return score
    starts = [a.start for a in adjustments]

    def find(q: float):
        i = bisect_right(starts, q + 1e-9) - 1
        return adjustments[i] if i >= 0 else None

    def map_q(q: float) -> float:
        a = find(q)
        if a is None:
            return q
        if q >= a.end - 1e-9:
            return q - a.q_before - ((a.end - a.start) * (1 - a.ratio))
        return q - a.q_before - (q - a.start) * (1 - a.ratio)

    # Time map: add breakpoints at the edges of adjusted measures so that
    # tempo is preserved on both sides, then remap every breakpoint.
    tm = score.time_map
    old = tm.changes
    quarters = {round(c.quarter, 6): c.quarter for c in old}
    for a in adjustments:
        for q in (a.start, a.end):
            quarters.setdefault(round(q, 6), q)
    new_changes = []
    known = {round(c.quarter, 6): c.time for c in old}
    for key in sorted(quarters):
        q = quarters[key]
        t = known[key] if key in known else tm.quarter_to_time(q)
        a = find(q)
        t_removed = 0.0
        if a is not None:
            span = (a.tend - a.tstart) if q >= a.end - 1e-9 else (t - a.tstart)
            t_removed = a.t_before + span * (1 - a.ratio)
        new_changes.append(MapQuarter(t - t_removed, map_q(q)))
    tm.changes = new_changes

    for ts in score.time_signatures:
        ts.quarters = map_q(ts.quarters)

    stack: List[Event] = [score]
    while stack:
        e = stack.pop()
        if e._onset is not None:
            onset = e._onset
            e._duration = map_q(onset + e._duration) - map_q(onset)
            e._onset = map_q(onset)
        if isinstance(e, EventGroup):
            stack.extend(e.content)

    if was_seconds:
        score.convert_to_seconds()
    return score
