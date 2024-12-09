"""Test suite for key profiles in `resources.key_profiles_literature.py`"""


import unittest

from musmart.resources.key_profiles_literature import source_list


class KeyProfileTest(unittest.TestCase):
    def test_string_attributes(self):
        """Every key profile should define `name`, `literature`, and `about` attributes as (non-empty) strings"""
        expected_attrs = ["name", "literature", "about"]
        for profile in source_list:
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
            for attr in profile.__dict__.keys():
                attr = getattr(profile, attr)
                # If the attribute is a list
                if isinstance(attr, list):
                    # Every element should be a floating point number
                    for element in attr:
                        self.assertIsInstance(element, float)
                    # TODO: we could probably test more things here
                    #  e.g., do we want to check that there are 11 values (for the 11 pitch classes?)

    def test_sum_attributes(self):
        """If we provide a `_sum` attribute, this should be normalised to sum to 1."""
        # Iterate over all the key profiles we've defined
        for profile in source_list:
            # Iterate over all the attributes in this class
            for attr in profile.__dict__.keys():
                # If we've defined an attribute ending with `_sum`
                if attr.endswith('_sum'):
                    # We'd expect the sum of this attribute to be approximately equal to 1.
                    summed = sum(getattr(profile, attr))
                    self.assertAlmostEquals(summed, 1., places=2)


if __name__ == '__main__':
    unittest.main()
