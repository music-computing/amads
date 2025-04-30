import unittest

from amads.core.utils import dir2coll, hz2num, keyname, num2hz
from amads.music import example


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

    def test_hz2num(self):
        """Test converting frequencies to MIDI key numbers."""
        print("-----------Testing hz2num function-----------")
        self.assertEqual(hz2num(440.0).num, 69)  # A4 (440 Hz) is MIDI key 69
        self.assertEqual(hz2num(880.0).num, 81)  # A5 (880 Hz) is MIDI key 81

    def test_num2hz(self):
        """Test converting MIDI key numbers to frequencies."""
        print("-----------Testing num2hz function-----------")
        self.assertAlmostEqual(num2hz(69), 440.0, places=2)  # MIDI key 69 is 440 Hz
        self.assertAlmostEqual(num2hz(81), 880.0, places=2)  # MIDI key 81 is 880 Hz

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
