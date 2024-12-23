"""
Tests for meter representation.

Tests functionality for regrouping and quantizing musical durations.
"""

import pytest

from amads.time.meter import (
    MetricalHierarchy,
    examples,
    starts_from_pulse_lengths,
    starts_from_ts,
    starts_from_ts_and_levels,
)


@pytest.fixture
def test_metres():
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
    return metres


def test_get_starts_from_ts_and_levels(test_metres):
    for tc in test_metres:
        t = starts_from_ts_and_levels(tc["ts"], tc["levels"])
        assert t == tc["starts"]


def test_pulse_lengths_to_start_list(test_metres):
    for tc in test_metres:
        t = starts_from_pulse_lengths(
            pulse_lengths=tc["pulses"], require_2_or_3_between_levels=False
        )
        assert t == tc["starts"]


def test_require_2_or_3():
    """Test a case with `require_2_or_3_between_levels` = True."""
    with pytest.raises(ValueError):
        starts_from_pulse_lengths(
            pulse_lengths=[4, 1], require_2_or_3_between_levels=True
        )


def test_start_hierarchy_from_ts():
    """Test start_hierarchy_from_ts by running through test cases."""
    for k in examples.start_hierarchy_examples:
        oh = starts_from_ts(k, minimum_pulse=32)
        assert oh == examples.start_hierarchy_examples[k]


"""Test various cases that should raise errors."""


def test_nothing():
    with pytest.raises(ValueError):
        MetricalHierarchy()


def test_levels_no_ts():
    with pytest.raises(ValueError):
        MetricalHierarchy(levels=[2, 1])


def test_invalid_denominator():
    with pytest.raises(ValueError):
        starts_from_ts("2/6")


def test_invalid_minimum_pulse():
    with pytest.raises(ValueError):
        starts_from_ts("2/4", minimum_pulse=17)


def test_level_beyond_6():
    with pytest.raises(ValueError):
        starts_from_ts_and_levels("2/4", levels=[7])


def test_pulse_beyond_measure_length():
    with pytest.raises(ValueError):
        starts_from_pulse_lengths([4, 2, 1], measure_length=2)


def test_require_2_3_fail():
    with pytest.raises(ValueError):
        starts_from_pulse_lengths([4, 1], require_2_or_3_between_levels=True)


def test_name_format():
    """
    One case in the correct format, and one that raises.
    """

    MetricalHierarchy("4/4", names={0.0: "ta", 1.0: "ka", 2.0: "di", 3.0: "mi"})

    with pytest.raises(AssertionError):
        MetricalHierarchy("4/4", names="Aditya, Bella, Carlos")

    with pytest.raises(AssertionError):
        MetricalHierarchy("4/4", names={0.0: ["Aditya", "Bella", "Carlos"]})
