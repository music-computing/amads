from typing import List

from ...core.basics import Concurrence, Note


class Slice(Concurrence):
    """A slice of a musical score between two timepoints.

    This is the base class for different slicing algorithms like salami slicing and
    windowing. A slice contains a list of notes that are sounding between its start
    and end times, as well as references to the original notes from which these
    were derived.

    Parameters
    ----------
    original_notes : List[Note]
        The original unmodified notes from which the slice notes were derived
    onset : float
        The start time offset of the slice
    duration : float
        The duration of the slice
    """

    def __init__(
        self,
        original_notes: List[Note],
        onset: float = 0,
        duration: float = 0,
    ):
        super().__init__(parent=None, onset=onset, duration=duration, content=[])
        self.original_notes = original_notes
