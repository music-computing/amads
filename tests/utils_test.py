"""Test utilities."""

import functools
import os
import unittest

import pytest

from amads.core.utils import dir2coll, hz2keynum, keyname, keynum2hz
from amads.music import example


def only_on_ci_job(job_name):
    """
    If the test is running on CI, skip it unless it's running on the specified CI job.

    Parameters
    ----------
    job_name : str
        Name of the CI job this test should run on

    Returns
    -------
    callable
        Decorator that skips the test if not on the specified CI job
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if os.environ.get("CI"):
                current_job = os.environ.get("GITHUB_JOB")
                if current_job != job_name:
                    pytest.skip(f"Test only runs on {job_name} CI job")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class TestUntils(unittest.TestCase):

    def setUp(self):
        """Set up the test case with example music files"""
        # Example music files
        self.midi_file = example.fullpath("midi/sarabande.mid")
        self.xml_file = example.fullpath("musicxml/ex1.xml")
        self.filenames = [str(self.midi_file), str(self.xml_file)]

    def test_dir2coll(self):
        """Test the dir2coll function"""
        print("-----------Testing dir2coll function-----------")
        scores = dir2coll(self.filenames)
        self.assertIsInstance(scores, dict)
        self.assertEqual(len(scores), 2)
        print("Scores extracted from files: ", scores.keys())

    def test_hz2keynum(self):
        """Test converting frequencies to MIDI key numbers."""
        print("-----------Testing hz2keynum function-----------")
        self.assertEqual(hz2keynum(440.0).keynum, 69)  # A4 (440 Hz) is MIDI key 69
        self.assertEqual(hz2keynum(880.0).keynum, 81)  # A5 (880 Hz) is MIDI key 81

    def test_keynum2hz(self):
        """Test converting MIDI key numbers to frequencies."""
        print("-----------Testing keynum2hz function-----------")
        self.assertAlmostEqual(keynum2hz(69), 440.0, places=2)  # MIDI key 69 is 440 Hz
        self.assertAlmostEqual(keynum2hz(81), 880.0, places=2)  # MIDI key 81 is 880 Hz

    def test_keyname(self):
        """Test converting key numbers to key names."""
        print("------- Testing keyname function--------------")

        # Test for 'nameoctave' (default) detail option
        self.assertEqual(keyname(60), "C4")  # MIDI key 60 should be 'C4'
        self.assertEqual(keyname(61), "C#4")  # MIDI key 61 should be 'C#4'
        self.assertEqual(keyname(69), "A4")  # MIDI key 69 should be 'A4'

        # Test for 'nameonly' detail option
        self.assertEqual(keyname(60, detail="nameonly"), "C")  # Just the note name
        self.assertEqual(keyname(61, detail="nameonly"), "C#")  # Just the note name
        self.assertEqual(keyname(69, detail="nameonly"), "A")  # Just the note name

        # Test list input with 'nameoctave'
        self.assertEqual(
            keyname([60, 61, 69]), ["C4", "C#4", "A4"]
        )  # List of MIDI keys

        # Test list input with 'nameonly'
        self.assertEqual(
            keyname([60, 61, 69], detail="nameonly"), ["C", "C#", "A"]
        )  # List of note names

        # Test edge cases
        self.assertEqual(keyname(0), "C-1")  # Lowest MIDI key
        self.assertEqual(keyname(127), "G9")  # Highest MIDI key

        # Test invalid detail option
        with self.assertRaises(ValueError):
            keyname(60, detail="invalid_option")


if __name__ == "__main__":
    unittest.main()
