import pytest

from amads.algorithms.mtype_tokenizer import FantasticTokenizer
from amads.core.basics import Score


def test_mtype_tokenizer():
    tokenizer = FantasticTokenizer()
    melody_1 = Score.from_melody(
        pitches=[62, 64, 65, 67, 64, 60, 62],  # D4, E4, F4, G4, E4, C4, D4
        durations=[
            0.5,
            0.5,
            0.5,
            0.5,
            1.0,
            0.5,
            0.5,
        ],  # quarter, eighth, quarter, eighth, eighth notes
    )

    # Test that MTypes are tokenized to correct length
    bigram_counts = tokenizer.get_mtype_counts(melody_1, method=2)
    for i in bigram_counts:
        assert len(i) == 2

    trigram_counts = tokenizer.get_mtype_counts(melody_1, method=3)
    for i in trigram_counts:
        assert len(i) == 3

    # Test that MTypes cannot be counted if method is larger than sequence length
    with pytest.raises(ValueError):
        tokenizer.get_mtype_counts(melody_1, method=10)

    # Test that MTypes cannot be counted if method n = 0
    with pytest.raises(ValueError):
        tokenizer.get_mtype_counts(melody_1, method=0)

    # Test that method="all" returns all MTypes
    all_counts = tokenizer.get_mtype_counts(melody_1, method="all")
    # Test each n-gram length by comparing to individual n-gram counts
    max_length = len(tokenizer.tokenize_phrase(tokenizer.phrases[0]))
    for n in range(1, max_length + 1):
        n_gram_counts = tokenizer.get_mtype_counts(melody_1, method=n)
        # Check that all n-grams of length n in n_gram_counts are also in all_counts
        for ngram in n_gram_counts:
            assert ngram in all_counts
            assert n_gram_counts[ngram] == all_counts[ngram]

    # We will make a new instance of the tokenizer to test the second melody,
    # using a phrase gap of 0.75 seconds
    tokenizer = FantasticTokenizer(phrase_gap=0.75)

    # Create a test melody which will be segmented into 2 phrases
    melody_2 = Score.from_melody(
        # Twinkle Twinkle Little Star
        pitches=[60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60],
        durations=[
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            1.0,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
        ],
    )

    # Test that the melody is segmented into 2 phrases
    tokenizer.get_mtype_counts(melody_2, method=2)
    assert len(tokenizer.phrases) == 2

    # The first phrase has 7 notes in so the maximum length MType is 6
    assert len(tokenizer.phrases[0]) == 7
    with pytest.raises(ValueError):
        tokenizer.get_mtype_counts(melody_2, method=7)

    # This is true of the second phrase as well
    assert len(tokenizer.phrases[1]) == 7
    with pytest.raises(ValueError):
        tokenizer.get_mtype_counts(melody_2, method=7)


if __name__ == "__main__":
    test_mtype_tokenizer()
