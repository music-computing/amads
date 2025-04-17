"""
Tests for meter representation.

Tests functionality for regrouping and quantizing musical durations.
"""

import pytest

from amads.time.meter import PulseLengths, StartTimeHierarchy, TimeSignature, examples

metres = []
for x in (
    (
        "4/4",
        [1, 2],
        [4, 2, 1],
        [[0.0, 4.0], [0.0, 2.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]],
    ),
    (
        "4/4",
        [3],
        [4, 0.5],
        [[0.0, 4.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]],
    ),
    (
        "6/8",
        [1, 2],
        [3, 1.5, 0.5],
        [[0.0, 3.0], [0.0, 1.5, 3.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]],
    ),
):
    new_dict = {"ts": x[0], "levels": x[1], "pulses": x[2], "starts": x[3]}
    metres.append(new_dict)


# def test_pulse_lengths_to_start_list(test_metres):
#     for tc in test_metres:
#         start_hierarchy = PulseLengths(pulse_lengths=tc["pulses"]).to_start_hierarchy()
#         assert start_hierarchy == tc["starts"]


def test_start_hierarchy_from_time_signature():
    """Test start_hierarchy_from_time_signature by running through test cases."""
    for example in examples.start_hierarchy_examples:
        ts = TimeSignature(as_string=example)
        ts.fill_2s_3s()
        sh = ts.to_start_hierarchy()
        sh = StartTimeHierarchy(start_hierarchy=sh)
        sh.add_faster_levels(minimum_beat_type=32)
        assert sh.start_hierarchy == examples.start_hierarchy_examples[example]


"""Test various cases that should raise errors and similar."""


def test_invalid_denominator():
    with pytest.raises(ValueError):
        TimeSignature(as_string="2/6")


def test_pulse_beyond_cycle_length():
    with pytest.raises(ValueError):
        PulseLengths([4, 2, 1], cycle_length=2)


def test_name_format():
    """
    One case in the correct format, and one that raises.
    """
    StartTimeHierarchy([[0.0, 0.1]], names={0.0: "ta", 1.0: "ka", 2.0: "di", 3.0: "mi"})

    with pytest.raises(AssertionError):
        StartTimeHierarchy([[0.0, 0.1]], names="Aditya, Bella, Carlos")

    with pytest.raises(AssertionError):
        StartTimeHierarchy([[0.0, 0.1]], names={0.0: ["Aditya", "Bella", "Carlos"]})
