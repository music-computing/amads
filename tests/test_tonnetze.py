"""
Tests for the Tonnetze modules.
"""

import pytest

from amads.core.basics import Chord, Note
from amads.harmony.tonnetze.a2 import A2VertexTonnetz


@pytest.fixture
def d_major_chord():
    """Fixture for a D major chord."""
    return [2, 62, 6, 9]


@pytest.fixture
def c_minor_chord():
    """Fixture for an A minor chord."""
    return [0, 3, 7]


def test_a2_vertex_tonnetz_init(d_major_chord):
    """Test initialization with a list of MIDI pitches."""
    euler = A2VertexTonnetz(d_major_chord)
    assert euler.pitch_multi_set == (2, 62, 6, 9)
    assert euler.pc_set == {2, 6, 9}
    assert euler.root == 2
    assert euler.major_not_minor is True


def test_a2_vertex_tonnetz_init_chord_object():
    """Test initialization with a Chord object."""
    chord = Chord(Note(pitch=60), Note(pitch=64), Note(pitch=67))
    euler = A2VertexTonnetz(chord)
    assert euler.root == 0
    assert euler.major_not_minor is True


def test_a2_vertex_tonnetz_leading_tone_exchange(d_major_chord):
    """Test leading tone exchange transformation."""
    euler = A2VertexTonnetz(d_major_chord)
    euler.leading_tone_exchange()
    assert euler.l_transform == (1, 61, 6, 9)


def test_a2_vertex_tonnetz_parallel(d_major_chord):
    """Test parallel transformation."""
    euler = A2VertexTonnetz(d_major_chord)
    euler.parallel()
    assert euler.p_transform == (2, 62, 5, 9)


def test_a2_vertex_tonnetz_relative(d_major_chord):
    """Test relative transformation."""
    euler = A2VertexTonnetz(d_major_chord)
    euler.relative()
    assert euler.r_transform == (2, 62, 6, 11)


# -------


def test_a2_vertex_tonnetz_init_a_minor(c_minor_chord):
    """Test initialization with an A minor chord."""
    euler = A2VertexTonnetz(c_minor_chord)
    assert euler.root == 0
    assert euler.major_not_minor is False


def test_a2_vertex_tonnetz_leading_tone_exchange_a_minor(c_minor_chord):
    """Test leading tone exchange with A minor."""
    euler = A2VertexTonnetz(c_minor_chord)
    euler.leading_tone_exchange()
    assert euler.l_transform == (0, 3, 8)


def test_a2_vertex_tonnetz_parallel_a_minor(c_minor_chord):
    """Test parallel transformation with A minor."""
    euler = A2VertexTonnetz(c_minor_chord)
    euler.parallel()
    assert euler.p_transform == (0, 4, 7)


def test_a2_vertex_tonnetz_relative_a_minor(c_minor_chord):
    """Test relative transformation with A minor."""
    euler = A2VertexTonnetz(c_minor_chord)
    euler.relative()
    assert euler.r_transform == (10, 3, 7)


def test_a2_vertex_tonnetz_invalid_chord():
    """
    Test initialization with an invalid chord (not a major or minor triad).
    Should raise `ValueError`.
    """
    with pytest.raises(ValueError):
        A2VertexTonnetz([0, 1, 2])
