"""Tests for keyname and keycode_from_kkkey."""

import pytest

from amads.pitch.key.keyname import keycode_from_kkkey, keyname


def test_keyname_major_c():
    assert keyname(1) == "C"


def test_keyname_minor_c():
    assert keyname(13) == "c"


def test_keyname_long_spelling():
    assert keyname(2, detail=False) == "C#/Db"
    assert keyname(14, detail=False) == "c#/db"


def test_keyname_list():
    assert keyname([1, 12, 13, 24]) == ["C", "B", "c", "b"]


def test_keyname_invalid_code():
    with pytest.raises(ValueError):
        keyname(0)
    with pytest.raises(ValueError):
        keyname(25)


def test_keycode_from_kkkey():
    assert keycode_from_kkkey("major", 0) == 1
    assert keycode_from_kkkey("minor", 1) == 14
    assert keyname(keycode_from_kkkey("major", 1)) == "C#"


def test_keycode_from_kkkey_invalid():
    with pytest.raises(ValueError):
        keycode_from_kkkey("dorian", 0)
    with pytest.raises(ValueError):
        keycode_from_kkkey("major", 12)
