"""
Calculates the tessitura constraint in Von Hippel's pitch approximation paper.

Ports the "tessitura" function from miditoolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 92.
"""

import heapq
import math
import statistics

from amads.core.basics import Note, Score


class _RunningMedian:
    """
    internal data structure for calculating the running median of a growing
    set of integers efficiently. This class leverages heapq, which constructs
    heaps from regular python lists.

    Attributes
    ----------
    min_heap : list[int]
        The heap containing the integers no smaller than the median
    max_heap : list[int]
        The heap containing the integers no larger than the median
    """

    def __init__(self):
        self.min_heap = []
        # because we still support python 3.11, we can't use the maxheap
        # facilities yet (introduced in 3.14), so that means we need to make all
        # the integers in this heap negative instead to support max_heap.
        self.max_heap = []

    def _internal_rebalance(self):
        min_heap_len = len(self.min_heap)
        max_heap_len = len(self.max_heap)
        if abs(min_heap_len - max_heap_len) <= 1:
            return

        assert abs(min_heap_len - max_heap_len) == 2

        if max_heap_len > min_heap_len:
            balance_val = heapq.heappop(self.max_heap)
            heapq.heappush(self.min_heap, -balance_val)
        else:
            balance_val = heapq.heappop(self.min_heap)
            heapq.heappush(self.max_heap, -balance_val)

    def insert_integer(self, new_data: int):
        if not self.min_heap or new_data > self.min_heap[0]:
            heapq.heappush(self.min_heap, new_data)
        else:
            heapq.heappush(self.max_heap, -new_data)
        self._internal_rebalance()

    def num_inserted(self) -> int:
        return len(self.min_heap) + len(self.max_heap)

    def obtain_current_median(self) -> int | float:
        min_heap_len = len(self.min_heap)
        max_heap_len = len(self.max_heap)
        assert abs(len(self.min_heap) - len(self.max_heap)) <= 1

        if min_heap_len < max_heap_len:
            return -self.max_heap[0]
        elif min_heap_len > max_heap_len:
            return self.min_heap[0]
        else:
            return (self.min_heap[0] + (-self.max_heap[0])) / 2


class _WelfordStdDev:
    """
    internal data structure for calculating the running standard deviation of a
    growing set of integers efficiently through Welford's algorithm.

    Attributes
    ----------
    sample_count : int
        total number of samples seen so far
    running_mean : float
        running mean of the scanned samples
    squared_accumulation : float
        squared accumulation of all samples seen so far
    """

    def __init__(self):
        self.sample_count = 0
        self.running_mean = 0.0
        self.squared_sum = 0.0

    def add_sample(self, sample: int):
        self.sample_count += 1
        old_mean = self.running_mean
        self.running_mean += (sample - self.running_mean) / self.sample_count
        self.squared_sum += (sample - self.running_mean) * (sample - old_mean)

    def remove_sample(self, sample: int):
        self.sample_count -= 1
        new_mean = self.running_mean
        self.running_mean -= (sample - self.running_mean) / self.sample_count
        self.squared_sum -= (sample - self.running_mean) * (sample - new_mean)

    def obtain_current_stdev(self) -> float:
        if self.sample_count < 2:
            return 0
        else:
            return math.sqrt(self.squared_sum / (self.sample_count - 1))


def _tessitura_miditoolbox(score: Score) -> Score | None:
    """
    Annotates the score with the tessitura constraint as specified by the
    miditoolbox implementation.

    Each note is annotated with "tessitura_ebm" if successful.

    Parameters
    ----------
    score : Score
        A monophonic and non-empty Score object.

    Returns
    -------
    Score | None
        An annotated score where each note is annotated with the given tessitura
        values. Or None if the score does not satisfy the preconditions.
    """
    note_iter = score.find_all(Note)
    start_note = next(note_iter, None)
    # Handle empty score
    if start_note is None:
        return None
    if not score.ismonophonic():
        return None

    # preprocess starting note
    median_tracker = _RunningMedian()
    median_tracker.insert_integer(start_note.midi_num)
    stdev_tracker = _WelfordStdDev()
    stdev_tracker.add_sample(start_note.midi_num)
    start_note.set("tessitura_mtb", 0)
    for idx, note in enumerate(note_iter):
        current_pitch = note.midi_num
        if idx == 0:
            tessitura_val = 0
        else:
            # obtain median
            current_median = median_tracker.obtain_current_median()
            # implement welford's algo here to bring this function down to
            # O(nlogn)
            current_stdev = stdev_tracker.obtain_current_stdev()
            tessitura_val = abs(
                (current_pitch - current_median) / current_stdev
            )
        note.set("tessitura_mtb", tessitura_val)
        # update running totals
        median_tracker.insert_integer(current_pitch)
        stdev_tracker.add_sample(note.midi_num)

    return score


def _tessitura_paper(score: Score) -> Score | None:
    """
    Annotates the score with the tessitura constraint as specified in Von
    Hippel's original paper.

    Each note is annotated with "tessitura" if successful.

    Parameters
    ----------
    score : Score
        A monophonic and non-empty Score object.

    Returns
    -------
    Score | None
        An annotated score where each note is annotated with the given tessitura
        values. Or None if the score does not satisfy the preconditions.
    """
    note_iter = score.find_all(Note)
    start_note = next(note_iter, None)
    # Handle empty score
    if start_note is None:
        return None
    if not score.ismonophonic():
        return None
    if next(note_iter, None):
        pitch_stdev = statistics.stdev(
            note.midi_num for note in score.find_all(Note)
        )
    else:
        pitch_stdev = math.inf

    pitch_mean = statistics.mean(note.midi_num for note in score.find_all(Note))
    for note in score.find_all(Note):
        tessitura_val = (note.midi_num - pitch_mean) / pitch_stdev
        note.set("tessitura", abs(tessitura_val))

    return score


def tessitura(
    score: Score, miditoolbox_compatible: bool = True
) -> Score | None:
    """
    Calculate the tessitura based on the standard deviation of pitch height.

    In Von Hippel's original paper, tessitura was defined as the pitch distance
    from the mean, scaled to number of standard deviations. Note that the
    mean and standard deviation here are defined over all the notes in the
    score.

    The paper analyzes the tessitura constraint through "scrambled twins," i.e.
    randomly generated melodies that have the same pitch distribution (and
    number of notes) as the original melody.
    This is done for two following reasons:
    (1) The set of all scrambled twins as a sample space is agnostic to the
    original melody's temporal pitch structure (i.e. features that are perceived
    specific to the original melody's sequence and tempo alignment).
    (2) The sample space of interval distributions mapped from the sample space
    of scrambled twins is correlated to the pitch distribution
    extracted from the original melody.
    Thus, by measuring the interval distribution from scrambled twins, we can
    measure the effect of the tessitura constraint on the original melody.

    This function ports the 'tessitura' function from miditoolbox. However,
    the original tessitura implementation in miditoolbox only takes a metric
    proportional to the median of the currently seen portion of the score and
    the currently accumulating standard deviation.
    If miditoolbox behavior is desired, just set the miditoolbox_compatible
    boolean to true.

    (1) The annotation for the notes in the score on the paper version is
    "tessitura"
    (2) The annotation for the backwards compatible version is "tessitura_mtb"

    Parameters
    ----------
    score : Score
        A monophonic and non-empty Score object.
    miditoolbox_compatible: bool
        A boolean indicating whether miditoolbox compatible behavior is desired.

    Returns
    -------
    Score | None
        An annotated score where each note is annotated with the given tessitura
        values. Or None if the score does not satisfy the preconditions.

    References
    ----------
    [1] von Hippel, P. (2000). Redefining pitch proximity: Tessitura and
        mobility as constraints on melodic interval size. Music Perception,
        17 (3), 315-327.
    """
    if miditoolbox_compatible:
        return _tessitura_miditoolbox(score)
    else:
        return _tessitura_paper(score)
