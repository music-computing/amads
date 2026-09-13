from amads.core.basics import Note, Score
from amads.melody.melodic_accent import melodic_accent


def test_empty_melody():
    """
    Test empty melody
    """
    empty_score = Score()
    assert melodic_accent(empty_score) is None


def test_melodic_peak():
    """
    Test accent values for a melody with a local peak pitch-change pattern
    """
    # Create a test score
    score = Score.from_melody([60, 64, 62])

    melodic_accent(score)
    desired_accents = [1, 0.83, 0.17]
    property = "melodic_accent"
    assert all(
        note.get(property=property, default=None) == desired
        for note, desired in zip(score.find_all(Note), desired_accents)
    )


def test_melodic_valley():
    """
    Test accent values for a melody with a local valley pitch-change pattern
    """
    score = Score.from_melody([64, 60, 65])

    melodic_accent(score)
    desired_accents = [1, 0.71, 0.29]
    property = "melodic_accent"
    assert all(
        note.get(property=property, default=None) == desired
        for note, desired in zip(score.find_all(Note), desired_accents)
    )


if __name__ == "__main__":
    test_empty_melody()
    test_melodic_peak()
    test_melodic_valley()
