"""
Projection of pitch-class distribution on a self-organizing map
(Toiviainen & Krumhansl, 2003)

Description:
    Presents an animation of multiple projections of a split event group
    onto a self-organizing map.

See https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=67 for more details
"""

# for function types
from collections.abc import Callable
from typing import Optional, Union

from matplotlib.figure import Figure

from amads.core.basics import Event, EventGroup
from amads.pitch.key import keysomdata as ksom


def split_set_by_time_constraints(
    event_set: EventGroup,
    onset_constraint: Callable[[Event, int], Optional[int]],
    offset_constraint: Callable[[Event, int], Optional[int]],
    truncate: bool,
):
    """
    Temporary time splitter for EventGroup (temporary until the actual version is finished).

    Very bad hackjob.
    """
    assert 0


def keysomanim(
    note_collection: EventGroup,
    map: Union[ksom.KeyProfileSOM, str],
    onset_constraint: Callable[[Event, int], Optional[int]],
    offset_constraint: Callable[[Event, int], Optional[int]],
    truncate: bool,
    has_legend: bool = True,
    show: bool = True,
) -> Figure:
    assert 0
