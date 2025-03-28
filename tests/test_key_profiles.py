"""Test suite for key profiles in `pitch.key.profiles.py`"""

import pytest

from amads.pitch.key.profiles import source_list


def test_string_attributes():
    """Every key profile should define `name`, `literature`, and `about` attributes as (non-empty) strings"""
    expected_attrs = ["name", "literature", "about"]
    for profile in source_list:
        # This dunder method should just be set to the name of the profile
        assert str(profile()) == profile().__str__() == getattr(profile, "name")
        # The name of the class should be the same as its .name attribute
        assert profile().__class__.__name__ == getattr(profile, "name")
        # The class should have all the desired attributes as non-empty strings
        for attr in expected_attrs:
            assert hasattr(profile, attr)
            assert isinstance(getattr(profile, attr), str)
            assert getattr(profile, attr) != ""


def test_array_attributes():
    """Check list attributes provided for each class"""
    for profile in source_list:
        # Iterate over every attribute for this profile
        for attr_key in profile.__dict__.keys():
            # Skip over this attribute, which gives us a tuple
            if attr_key == "__match_args__":
                continue
            # Get the values of attribute
            attr_val = getattr(profile, attr_key)
            # Every element of tuples should be a floating point number
            #  We should have 12 of them, one per key
            if isinstance(attr_val, tuple):
                assert all(isinstance(element, float) for element in attr_val)
                assert len(attr_val) == 12


def test_sum_attributes():
    """If we provide a `_sum` attribute, this should be normalised to sum to 1."""
    # Iterate over all the key profiles we've defined
    for profile in source_list:
        # Iterate over all the attributes in this class
        for attr in profile.__dict__.keys():
            # If we've defined an attribute ending with `_sum`
            if attr.endswith("_sum"):
                # We'd expect the sum of this attribute to approximately equal 1.
                summed = sum(getattr(profile, attr))
                assert pytest.approx(summed, rel=1e-2) == 1.0


def test_missing_attributes():
    """Test that we raise errors properly when trying to access missing attributes"""
    for profile in source_list:
        with pytest.raises(AttributeError):
            _ = profile().__getitem__("missing")
