from amads.algorithms.concur import concur
from amads.core.basics import Note, Part, Score


def test_concur():
    """Test that the concur function correctly calculates the proportion of distinct onset groups to total onsets with a given threshold"""

    # Setup our test data
    test_score = Score()
    test_part = Part(parent=test_score)

    Note(parent=test_part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=test_part, onset=0.1, duration=1.0, pitch=60)
    Note(parent=test_part, onset=0.3, duration=1.0, pitch=60)
    Note(parent=test_part, onset=1.0, duration=2.0, pitch=60)

    # Run concur() function with a threshold of 0.2
    concurrency = concur(test_score, threshold=0.2)

    # There are 4 notes and 3 distinct onset groups (0.0 and 0.1 are grouped together, 0.3 is separate, and 1.0 is separate)
    assert concurrency == 3 / 4


def test_concur_all_concurrent():
    """Test that concur returns the correct proportion when all notes are concurrent"""
    test_score = Score()
    test_part = Part(parent=test_score)

    Note(parent=test_part, onset=0.0, duration=1.0, pitch=60)
    Note(parent=test_part, onset=0.1, duration=1.0, pitch=62)
    Note(parent=test_part, onset=0.15, duration=1.0, pitch=64)

    # All 3 notes are within threshold of each other
    assert concur(test_score, threshold=0.2) == 1 / 3


if __name__ == "__main__":
    test_concur()
    test_concur_all_concurrent()
