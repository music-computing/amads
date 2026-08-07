"""
Calculates the tessitura constraint in Von Hippel's pitch approximation paper.

Ports the "tessitura" function from miditoolbox.

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 92.
"""

import heapq
import math
import statistics

from amads.core.basics import Note, Score

__author__ = "Yiwen Zhao"

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

    def insert_integer(self, new_data : int):
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

    def add_sample(self, sample : int):
        self.sample_count += 1
        old_mean = self.running_mean
        self.running_mean += (sample - self.running_mean) / self.sample_count
        self.squared_sum += (sample - self.running_mean) * (sample - old_mean)

    def remove_sample(self, sample : int):
        self.sample_count -= 1
        new_mean = self.running_mean
        self.running_mean -= (sample - self.running_mean) / self.sample_count
        self.squared_sum -= (sample - self.running_mean) * (sample - new_mean)

    def obtain_current_stdev(self) -> float:
        if (self.sample_count < 2):
            return 0
        else:
            return math.sqrt(self.squared_sum / (self.sample_count - 1))

def tessitura(score: Score) -> Score | None:
    """
    Calculate the tessitura based on the standard deviation of pitch height.

    In Von Hippel's original paper, tessitura was defined as the distance,
    indexed in number of standard deviations from the mean (in other words,
    scaled by dividing the standard deviation of pitches of the entire melody).

    Agnostic to melodic structure, the paper analyzes "scrambled twins," or
    randomly generated melodies that have the same pitch distribution as the
    original melody. Thus, the intervals present in a randomly generated paper
    is wholly a product of the tessitura constraint.

    This function ports the 'tessitura' function from miditoolbox. However,
    our behavior differs because the tessitura miditoolbox implements
    only takes a metric proportional to the median of the currently seen portion
    of the score as we iterate over the algorithm.

    Parameters
    ----------
    score : Score
        A monophonic and non-empty Score object.

    Returns
    -------
    Score | None
        An annotated score where each note is annotated with the tessitura
        values. Or None if the score does not satisfy the preconditions.

    References
    ----------
    [1] von Hippel, P. (2000). Redefining pitch proximity: Tessitura and 
        mobility as constraints on melodic interval size. Music Perception, 
        17 (3), 315-327. 
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
    median_tracker.insert_integer(start_note.key_num)
    stdev_tracker = _WelfordStdDev()
    stdev_tracker.add_sample(start_note.key_num)
    start_note.set("tessitura", 0)
    for idx, note in enumerate(note_iter):
        current_pitch = note.key_num
        if idx == 0:
            note.set("tessitura", 0)
        else:
            # obtain median
            current_median = median_tracker.obtain_current_median()
            # implement welford's algo here to bring this function down to
            # O(nlogn)
            current_stdev = stdev_tracker.obtain_current_stdev()
            tessitura_val = (current_pitch - current_median) / current_stdev
            note.set("tessitura", abs(tessitura_val))
        # update running totals
        median_tracker.insert_integer(current_pitch)
        stdev_tracker.add_sample(note.key_num)

    return score
