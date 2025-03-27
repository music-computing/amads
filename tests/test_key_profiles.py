"""Test suite for key profiles in `pitch.key.profiles.py`"""

import unittest

from amads.pitch.key.profiles import source_list


class KeyProfileTest(unittest.TestCase):
    def test_string_attributes(self):
        """Every key profile should define `name`, `literature`, and `about` attributes as (non-empty) strings"""
        expected_attrs = ["name", "literature", "about"]
        for profile in source_list:
            # This dunder method should just be set to the name of the profile
            self.assertTrue(
                str(profile()) == profile().__str__() == getattr(profile, "name")
            )
            for attr in expected_attrs:
                # The class should have the attribute
                self.assertTrue(hasattr(profile, attr))
                # The attribute should be a string type
                self.assertIsInstance(getattr(profile, attr), str)
                # The attribute should not be an empty string
                self.assertTrue(getattr(profile, attr) != "")

    def test_array_attributes(self):
        """Check list attributes provided for each class"""
        for profile in source_list:
            # Iterate over every attribute for this profile
            for attr_key in profile.__dict__.keys():
                # Skip over this attribute, which gives us a tuple of all defined attributes
                if attr_key == "__match_args__":
                    continue
                # Get the values of the attribute
                attr_val = getattr(profile, attr_key)
                # If the attribute is a list
                if isinstance(attr_val, tuple):
                    # Every element should be a floating point number
                    for element in attr_val:
                        self.assertIsInstance(element, float)
                    self.assertEqual(len(attr_val), 12)

    def test_sum_attributes(self):
        """If we provide a `_sum` attribute, this should be normalised to sum to 1."""
        # Iterate over all the key profiles we've defined
        for profile in source_list:
            # Iterate over all the attributes in this class
            for attr in profile.__dict__.keys():
                # If we've defined an attribute ending with `_sum`
                if attr.endswith("_sum"):
                    # We'd expect the sum of this attribute to be approximately equal to 1.
                    summed = sum(getattr(profile, attr))
                    self.assertAlmostEquals(summed, 1.0, places=2)

    def test_missing_attributes(self):
        """Test that we raise errors properly when trying to access missing attributes"""
        for profile in source_list:
            with self.assertRaises(AttributeError):
                _ = profile().__getitem__("missing")
