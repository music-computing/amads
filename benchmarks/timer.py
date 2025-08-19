"""timer to measure and report execution times"""
# flake8: noqa E303

__author__ = "Roger B. Dannenberg"

import time
from typing import Optional


class Timer:
    """A simple timer class to measure execution time.
    """
    def __init__(self, label: Optional[str] = None):
        self.init(label or "execution time")


    def init(self, label: Optional[str] = None):
        """Initialize the timer.
        If label is None, use existing label, which defaults to
        "execution time".
        """
        if label:
            self.label = label
        self.start_time = None
        self.end_time = None
        self.total_time = 0.0
        self.n = 0
        self.initialized = True


    def start(self, reset: Optional[bool] = False):
        """Start the timer."""
        if reset:
            self.init()
        self.start_time = time.perf_counter()


    def stop(self, report: bool = False) -> float:
        """Stop the timer and return the elapsed time."""
        self.end_time = time.perf_counter()
        elapsed_time = self.end_time - self.start_time
        self.total_time += elapsed_time
        self.n += 1
        self.end_time = None  # will error if stop before start
        if report:
            return self.report()
        return elapsed_time


    def report(self) -> float:
        """Report the total and average time."""
        average_time = self.total_time / self.n
        print(f"Total {self.label}: {self.total_time:.6f} seconds")
        if self.n > 1:
            print(f"Average {self.label}: {average_time:.6f} seconds")
        return average_time


    def time_it(self, func, label, n: int = 1,
                args: list[any] = [], kwargs: dict = {}):
        """Time a function call."""
        self.init(label)
        for _ in range(n):
            self.start()
            func(*args, **kwargs)
            self.stop()
        return self.report()
