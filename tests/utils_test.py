import unittest

from amads.core.utils import (
    dir_to_collection,
    hz_to_key_num,
    key_num_to_hz,
    key_num_to_name,
)
from amads.music import example


class TestUntils(unittest.TestCase):

    def setUp(self):
        """Set up the test case with example music files"""
        # Example music files
        self.midi_file = example.fullpath("midi/sarabande.mid")
        self.xml_file = example.fullpath("musicxml/ex2.xml")
        self.filenames = [str(self.midi_file), str(self.xml_file)]

    def test_dir_to_collection(self):
        """Test the dir_to_collection function"""
        print("-----------Testing dir_to_collection function-----------")
        scores = dir_to_collection(self.filenames)
        self.assertIsInstance(scores, dict)
        self.assertEqual(len(scores), 2)
        print("Scores extracted from files: ", scores.keys())

    def test_hz_to_key_num(self):
        """Test converting frequencies to MIDI key numbers."""
        print("-----------Testing hz_to_key_num function-----------")
        self.assertEqual(hz_to_key_num(440.0), 69)  # A4 (440 Hz) is MIDI key 69
        self.assertEqual(hz_to_key_num(880.0), 81)  # A5 (880 Hz) is MIDI key 81

    def test_key_num_to_hz(self):
        """Test converting MIDI key numbers to frequencies."""
        print("-----------Testing key_num_to_hz function-----------")
        self.assertAlmostEqual(
            key_num_to_hz(69), 440.0, places=2
        )  # MIDI key 69 is 440 Hz
        self.assertAlmostEqual(
            key_num_to_hz(81), 880.0, places=2
        )  # MIDI key 81 is 880 Hz

    def test_key_num_to_name(self):
        """Test converting key numbers to key names."""
        print("------- Testing key_num_to_name function--------------")

        # Test for 'nameoctave' (default) detail option
        self.assertEqual(
            key_num_to_name(60), "C4"
        )  # MIDI key 60 should be 'C4'
        self.assertEqual(
            key_num_to_name(61), "C#4"
        )  # MIDI key 61 should be 'C#4'
        self.assertEqual(
            key_num_to_name(69), "A4"
        )  # MIDI key 69 should be 'A4'

        # Test for 'nameonly' detail option
        self.assertEqual(
            key_num_to_name(60, detail="nameonly"), "C"
        )  # Just the note name
        self.assertEqual(
            key_num_to_name(61, detail="nameonly"), "C#"
        )  # Just the note name
        self.assertEqual(
            key_num_to_name(69, detail="nameonly"), "A"
        )  # Just the note name

        # Test list input with 'nameoctave'
        self.assertEqual(
            key_num_to_name([60, 61, 69]), ["C4", "C#4", "A4"]
        )  # List of MIDI keys

        # Test list input with 'nameonly'
        self.assertEqual(
            key_num_to_name([60, 61, 69], detail="nameonly"), ["C", "C#", "A"]
        )  # List of note names

        # Test edge cases
        self.assertEqual(key_num_to_name(0), "C-1")  # Lowest MIDI key
        self.assertEqual(key_num_to_name(127), "G9")  # Highest MIDI key

        # Test invalid detail option
        with self.assertRaises(ValueError):
            key_num_to_name(60, detail="invalid_option")


if __name__ == "__main__":
    unittest.main()
