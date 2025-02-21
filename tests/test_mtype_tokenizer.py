import pytest

from amads.algorithms.mtype_tokenizer import FantasticTokenizer, MType
from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Score


def test_mtype_tokenizer():
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

    # Initialize tokenizer and counter
    tokenizer = FantasticTokenizer()
    ngrams = NGramCounter()

    # Tokenize melody and count n-grams
    tokenizer.tokenize_melody(melody_1)
    bigram_counts = ngrams.count_ngrams(tokenizer.tokens, method=2)
    for ngram in bigram_counts:
        assert len(ngram) == 2

    trigram_counts = ngrams.count_ngrams(tokenizer.tokens, method=3)
    for ngram in trigram_counts:
        assert len(ngram) == 3

    # Test that n-grams cannot be counted if method is larger than sequence length
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokenizer.tokens, method=10)

    # Test that n-grams cannot be counted if method n = 0
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokenizer.tokens, method=0)

    # Test that method="all" returns all n-grams
    all_counts = ngrams.count_ngrams(tokenizer.tokens, method="all")
    # Test each n-gram length by comparing to individual n-gram counts
    max_length = max(len(ngram) for ngram in all_counts)
    for n in range(1, max_length + 1):
        n_gram_counts = ngrams.count_ngrams(tokenizer.tokens, method=n)
        # Check that all n-grams of length n in n_gram_counts are also in all_counts
        for ngram in n_gram_counts:
            assert ngram in all_counts
            assert n_gram_counts[ngram] == all_counts[ngram]

    # Test with a second melody using a different phrase gap
    tokenizer = FantasticTokenizer(phrase_gap=0.75)
    ngrams = NGramCounter()

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
    tokenizer.tokenize_melody(melody_2)
    ngrams.count_ngrams(tokenizer.tokens, method=2)
    # The first phrase has 7 notes in so the maximum length n-gram is 6
    assert len(tokenizer.phrases[0]) == 7
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokenizer.tokens[0], method=7)

    # This is true of the second phrase as well
    assert len(tokenizer.phrases[1]) == 7
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokenizer.tokens[0], method=7)


def test_mtype_encodings():
    possible_interval_classes = FantasticTokenizer.interval_classes

    assert "d3" in possible_interval_classes
    assert "u5" in possible_interval_classes
    assert None in possible_interval_classes

    possible_ioi_ratio_classes = FantasticTokenizer.ioi_ratio_classes

    assert "q" in possible_ioi_ratio_classes
    assert "e" in possible_ioi_ratio_classes
    assert "l" in possible_ioi_ratio_classes
    assert None in possible_ioi_ratio_classes

    mtypes = []
    for interval_class in possible_interval_classes:
        for ioi_ratio_class in possible_ioi_ratio_classes:
            mtype = MType(interval_class, ioi_ratio_class)
            mtypes.append(mtype)

            assert isinstance(mtype.integer, int)
            assert mtype.integer >= 0

    assert len(mtypes) == len(set(mtypes))

    integers = [mtype.integer for mtype in mtypes]
    assert len(integers) == len(set(integers))

    for integer in integers:
        assert 0 <= integer <= len(integers) - 1


def test_ngram_counts():

    simple_list = [0, 1, 1, 0, 1]
    ngrams = NGramCounter()

    # Features calculated from the ngrams are not available until ngrams are counted
    with pytest.raises(ValueError):
        _ = ngrams.yules_k

    # Count the ngrams
    ngrams.count_ngrams(simple_list, method=2)
    assert ngrams.ngram_counts == {("0", "1"): 2, ("1", "1"): 1, ("1", "0"): 1}

    # Now the features are available
    assert ngrams.yules_k is not None


if __name__ == "__main__":
    test_mtype_tokenizer()
    test_mtype_encodings()
    test_ngram_counts()
