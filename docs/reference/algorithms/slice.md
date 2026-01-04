The `algorithms/slice` directory contains software pertaining
to breaking scores into sequences of “vertical slices,” e.g,
the portions of all notes within a sequence of time intervals.

In the “Salami Slice” algorithm, time intervals are non-overlapping
and their boundaries are all note onset and offset times. A list of
slices can be created by calling the
[`salami_slice`](#amads.algorithms.slice.salami.salami_slice) function.
The returned slices are instances of the
[`Slice`](#amads.algorithms.slice.slice.Slice) class.

A more basic way to slice a score is to construct a
[`Window`](#amads.algorithms.slice.window.Window), which is basically
just a [`Slice`](#amads.algorithms.slice.slice.Slice) with a special
constructor that selects and clips notes that fall within a given
time interval, resulting in a single slice. You can create a sequence
of [`Window`](#amads.algorithms.slice.window.Window)s
using any criteria for time intervals, including overlapping windows.


::: amads.algorithms.slice.salami
    options:
      members: []

----------------

::: amads.algorithms.slice.salami.Timepoint 

----------------

::: amads.algorithms.slice.salami.salami_slice

----------------

::: amads.algorithms.slice.slice.Slice
    options: 
      inherited_members: false 

----------------

::: amads.algorithms.slice.window.Window
    options: 
      inherited_members: false

::: amads.algorithms.slice.window.sliding_window
