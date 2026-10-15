"""Tests for tonal_stability."""

import pytest

from amads.core.basics import Note, Score
from amads.pitch.key import profiles as prof
from amads.pitch.key.tonal_stability import tonal_stability
from amads.pitch.key.tonality import tonality


def test_tonal_stability_c_major_scale_on_notes():
    """Test that a C major scale receives KK major profile weights on each note."""
    score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    tonal_stability(score)
    notes = score.get_sorted_notes()
    expected = [
        prof.krumhansl_kessler.major.data[i] for i in (0, 2, 4, 5, 7, 9, 11, 0)
    ]
    for note, value in zip(notes, expected):
        assert note.get("tonal_stability") == pytest.approx(value)


def test_tonal_stability_matches_tonality_for_c_major():
    """Test that annotated values match tonality() for a C major melody."""
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    score_list = Score.from_melody(pitches)
    score_annot = Score.from_melody(pitches)
    list_values = tonality(score_list)
    tonal_stability(score_annot)
    note_values = [
        n.get("tonal_stability") for n in score_annot.get_sorted_notes()
    ]
    assert note_values == pytest.approx(list_values)


def test_tonal_stability_g_major_key_index_7():
    """Test that G receives the tonic weight when key_index is 7."""
    score = Score.from_melody([67, 69, 71, 72, 74, 76, 78, 79])
    tonal_stability(score, key=("major", 7))
    g_note = score.get_sorted_notes()[0]
    assert g_note.get("tonal_stability") == pytest.approx(
        prof.krumhansl_kessler.major.data[0]
    )


def test_tonal_stability_differs_from_tonality_on_g_major():
    """Test that G major stability differs from tonality (C-tonic midi tool box behavior)."""
    pitches = [67, 69, 71, 72, 74, 76, 78, 79]
    score_mtb = Score.from_melody(pitches)
    score_amads = Score.from_melody(pitches)
    mtb_values = tonality(score_mtb)
    tonal_stability(score_amads, key=("major", 7))
    amads_values = [
        n.get("tonal_stability") for n in score_amads.get_sorted_notes()
    ]
    assert amads_values != pytest.approx(mtb_values)


def test_tonal_stability_estimates_key_without_override():
    """Test that kkkey estimates key when key= is not given."""
    pitches = [67, 69, 71, 72, 74, 76, 78, 79]
    score_auto = Score.from_melody(pitches)
    score_fixed = Score.from_melody(pitches)
    tonal_stability(score_auto)  # should estimate key automatically
    tonal_stability(
        score_fixed, key=("major", 7)
    )  # should use key=("major", 7)
    auto_values = [
        n.get("tonal_stability") for n in score_auto.get_sorted_notes()
    ]
    fixed_values = [
        n.get("tonal_stability") for n in score_fixed.get_sorted_notes()
    ]
    assert auto_values == pytest.approx(fixed_values)  # should be the same


def test_tonal_stability_multiple_prop_names_coexist():
    """Test that multiple stability properties can coexist on the same score."""
    score = Score.from_melody([60, 64, 67])
    tonal_stability(
        score,
        profile=prof.krumhansl_kessler,
        stability_prop_name="tonal_stability_kk",
    )
    tonal_stability(
        score,
        profile=prof.temperley,
        stability_prop_name="tonal_stability_temperley",
    )
    note = score.get_sorted_notes()[0]
    assert note.get("tonal_stability_kk") is not None
    assert note.get("tonal_stability_temperley") is not None
    assert note.get("tonal_stability_kk") != note.get(
        "tonal_stability_temperley"
    )


def test_tonal_stability_empty_score():
    """Test that an empty score is returned unchanged."""
    score = Score.from_melody([])
    result = tonal_stability(score)
    assert result is score
    assert score.get_sorted_notes() == []


def test_tonal_stability_key_override():
    """Test that key= skips kkkey and uses the given attribute and key_index."""
    score = Score.from_melody([67, 69, 71])
    tonal_stability(score, key=("major", 7))
    for note in score.get_sorted_notes():
        pc = int(note.pitch.midi_num) % 12
        degree = (pc - 7) % 12  # scale degree in the key of G major
        assert note.get("tonal_stability") == pytest.approx(
            prof.krumhansl_kessler.major.data[degree]
        )


def test_tonal_stability_vuvan_attribute_not_major_minor():
    """Test that a non-major/minor profile attribute works with key=."""
    score = Score.from_melody([60, 62, 63, 65, 67, 68, 70, 72])
    tonal_stability(score, profile=prof.vuvan, key=("natural_minor", 0))
    for note in score.get_sorted_notes():
        pc = int(note.pitch.midi_num) % 12
        assert note.get("tonal_stability") == pytest.approx(
            prof.vuvan.natural_minor.data[pc]
        )


def test_tonal_stability_vuvan_estimates_among_its_attributes():
    """Test that kkkey can choose among all attributes on a Vuvan profile."""
    score = Score.from_melody([60, 62, 63, 65, 67, 68, 70, 72])
    tonal_stability(score, profile=prof.vuvan)
    for note in score.get_sorted_notes():
        assert note.get("tonal_stability") is not None


def test_tonal_stability_annotates_tied_head_only_in_place():
    """Test that the head of a tied group is annotated in place."""
    score = Score.from_melody([60, 60])
    head, tied_to = list(score.find_all(Note, include_tied_to_notes=True))
    head.tie = tied_to
    tonal_stability(score, key=("major", 0))
    expected = prof.krumhansl_kessler.major.data[0]
    assert head.get("tonal_stability") == pytest.approx(expected)
    assert tied_to.get("tonal_stability") is None
    assert score.get_sorted_notes() == [head]


def test_tonal_stability_invalid_attribute_raises():
    """Test that an invalid profile attribute raises ValueError."""
    score = Score.from_melody([60])
    with pytest.raises(ValueError, match="PitchProfile attribute"):
        tonal_stability(score, key=("not_a_mode", 0))


def test_tonal_stability_invalid_key_index_raises():
    """Test that an out-of-range key_index raises ValueError."""
    score = Score.from_melody([60])
    with pytest.raises(ValueError, match="key_index must be 0..11"):
        tonal_stability(score, key=("major", 12))


def test_tonal_stability_undefined_pitch_raises():
    """Test that a note without pitch raises ValueError."""
    score = Score.from_melody([60, 62])
    score.get_sorted_notes()[0].pitch = None
    with pytest.raises(ValueError, match="defined pitch"):
        tonal_stability(score, key=("major", 0))
