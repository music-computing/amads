"""
How big is a note? Do a bunch of allocations and plot memory usage.
This code is for making some specific measurements and is not
intended to be a general-purpose tool or a supported component of AMADS.
"""
# fmt: off
# flake8: noqa E129,E303

__author__ = "Roger B. Dannenberg"

import gc
import sys
import tracemalloc

import matplotlib.pyplot as plt
import psutil

# from memory_profiler import memory_usage
from amads.core import Note

"""
How big is a note?
"""
import sys


def get_total_size(obj, seen=None):
    """Recursively find the total memory size of an object, including its attributes.
    This implements a specific definition of "size" which may or may not be equivalent
    to that of https://pypi.org/project/objsize/. The tests below measuring the entire
    process memory footprint seems more useful since actual memory usage includes
    fragmentation and other overhead that is not included in the size of an object. 
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    if isinstance(obj, str):
        return size
    if isinstance(obj, dict):
        size += sum([get_total_size(v, seen) for v in obj.values()])
        size += sum([get_total_size(k, seen) for k in obj.keys()])
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_total_size(i, seen) for i in obj)
    else:
        if hasattr(obj, '__dict__'):
            size += get_total_size(obj.__dict__, seen)
        if hasattr(obj.__class__, '__slots__'):  # For objects with __slots__
            size += sum(get_total_size(getattr(obj, s), seen) for s in obj.__class__.__slots__ if hasattr(obj, s))
    return size


# Example usage
from amads.core import Note


def get_process_memory():
    """Get the total memory used by the current process."""
    import os
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss  # Resident Set Size: the non-swapped physical memory the process has used

# Get the initial memory usage before allocations
start_size = get_process_memory()
start_swapout = psutil.swap_memory().sout
print(f"Initial memory used by the process: {start_size} bytes")

allocated = [None] * 100
note_store = [None] * 100

# Start tracing memory allocations
tracemalloc.start()

for i in range(100):
    gc.collect()  # Collect garbage to ensure accurate memory usage measurement
    # Get the current memory usage
    current, peak = tracemalloc.get_traced_memory()
    allocated[i] = (i, current, peak, get_process_memory() - start_size, 
                    psutil.swap_memory().sout - start_swapout)
    note_store[i] = [Note() for i in range(100000)]

# Stop tracing memory allocations
tracemalloc.stop()

sout = psutil.swap_memory().sout - start_swapout
print(f"Total memory used by n: {get_total_size(Note())} bytes")
print(f"Total memory added by the process: {get_process_memory() - start_size} bytes")
print(f"Total swapout: {sout} bytes")

for data in allocated:
    print(data)

# Extract data for plotting
counts = [data[0] for data in allocated]
peaks = [data[2] / 1024 / 1024 for data in allocated]  # Convert to MB
memories = [data[3] / 1024 / 1024 for data in allocated]  # Convert to MB
swapped = [data[4] / 1024 / 1024 for data in allocated]  # Convert to MB

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(counts, peaks, label='Peak Memory (MB)', color='blue')
plt.plot(counts, memories, label='Memory Added (MB)', color='green')
plt.plot(counts, swapped, label='Swapped (MB)', color='red')
plt.xlabel('Count')
plt.ylabel('Memory (MB)')
plt.title('Memory Usage and Swapping as a Function of Count')
plt.legend()
plt.grid(True)
plt.show()
plt.ylabel('Memory (MB)')
plt.title('Memory Usage and Swapping as a Function of Allocations (100,000 Notes)')
plt.legend()
plt.grid(True)
plt.show()
