"""Test suite for key profiles in `pitch.key.profiles.py`"""

from dataclasses import fields

import pytest

from amads.pitch.key.profiles import PitchProfile, source_list


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


def test_data_attributes():
    """Check attributes provided for each dataclass"""
    for profile in source_list:
        attribute_names = [f.name for f in fields(profile)]
        # Iterate over every attribute for this profile
        for attr_key in attribute_names:
            # Skip over this attribute, which gives us a tuple
            if attr_key == "__match_args__":
                continue
            # Get the values of attribute
            attr_val = getattr(profile, attr_key)
            # Skip over reserved metadata attribute names
            if attr_key in ["name", "literature", "about"]:
                assert isinstance(attr_val, str)
            # Every element of tuples should be a floating point number
            #  We should have 12 of them, one per key
            elif isinstance(attr_val, tuple):
                assert len(attr_val) == 12
                for elem in attr_val:
                    if not isinstance(elem, PitchProfile):
                        print(
                            f"Attribute {attr_key} of profile {profile.__name__} "
                            f"has non-PitchProfile element: {elem} ({type(elem)})"
                        )
                assert all(isinstance(elem, PitchProfile) for elem in attr_val)
            else:
                assert isinstance(attr_val, PitchProfile)


def test_missing_attributes():
    """Test that we raise errors properly when trying to access missing attributes"""
    for profile in source_list:
        with pytest.raises(AttributeError):
            _ = profile().__getitem__("missing")
