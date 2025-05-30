import warnings

import pytest

from amads.algorithms.mtype_tokenizer import FantasticTokenizer, MType
from amads.algorithms.ngrams import NGramCounter
from amads.core.basics import Score
from amads.melody.segment import fantastic_segmenter


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
    tokens = tokenizer.tokenize(melody_1)

    # Count bigrams
    ngrams.count_ngrams(tokens, n=2)
    for ngram in ngrams.get_counts():
        assert len(ngram) == 2

    # Reset counter, count trigrams
    ngrams.reset()
    ngrams.count_ngrams(tokens, n=3)
    for ngram in ngrams.get_counts():
        assert len(ngram) == 3

    # Test that n-grams cannot be counted if method is larger than sequence length
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokens, n=10)

    # Test that n-grams cannot be counted if method n = 0
    with pytest.raises(ValueError):
        ngrams.count_ngrams(tokens, n=0)

    # Test that n=None returns all n-grams
    ngrams.reset()
    ngrams.count_ngrams(tokens, n=None)
    all_counts = ngrams.get_counts()
    # Test each n-gram length by comparing to individual n-gram counts
    max_length = max(len(ngram) for ngram in all_counts)
    for n in range(1, max_length + 1):
        ngrams.reset()
        ngrams.count_ngrams(tokens, n=n)
        n_gram_counts = ngrams.get_counts()
        # Check that all n-grams of length n in n_gram_counts are also in all_counts
        for ngram in n_gram_counts:
            assert ngram in all_counts
            assert n_gram_counts[ngram] == all_counts[ngram]

    # Test with a second melody using a different phrase gap
    tokenizer = FantasticTokenizer()
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

    # Test that the melody is segmented into phrases
    segments = fantastic_segmenter(melody_2, phrase_gap=0.75, units="quarters")

    # Test counting all n-grams across segments
    ngrams.reset()
    for segment in segments:
        segment_tokens = tokenizer.tokenize(segment)
        ngrams.count_ngrams(segment_tokens, n=None)

    # Get all n-gram counts
    all_counts = ngrams.get_counts()

    # Test that we can't count n-grams longer than sequence
    max_length = max(len(ngram) for ngram in all_counts)

    # As the phrase length is 7 notes, the maximum length n-gram is 6
    assert max_length == 6
    with pytest.raises(ValueError):
        ngrams.count_ngrams(segment_tokens, n=max_length + 1)


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
    complex_list = [0, 1, 2, 3, 4, 5]
    simple_ngrams = NGramCounter()
    complex_ngrams = NGramCounter()

    # Features calculated from the ngrams are not available until ngrams are counted
    with pytest.raises(ValueError):
        _ = simple_ngrams.yules_k

    # Count the ngrams
    simple_ngrams.count_ngrams(simple_list, n=2)
    assert simple_ngrams.get_counts() == {("0", "1"): 2, ("1", "1"): 1, ("1", "0"): 1}

    # Now the features are available
    assert simple_ngrams.yules_k is not None

    complex_ngrams.count_ngrams(complex_list, n=2)

    # We expect that Yule's K is lower for the complex list, as there is more variety in the n-grams
    # Yule's K takes a higher value for more repetitive sequences
    assert complex_ngrams.yules_k < simple_ngrams.yules_k

    # Simpson's D should also be higher for more repetitive sequences
    assert complex_ngrams.simpsons_d < simple_ngrams.simpsons_d

    # Sichel's S should also be higher for more the simple list,
    # as complex_list contains no n-grams that occur exactly twice
    assert complex_ngrams.sichels_s < simple_ngrams.sichels_s

    # Honore's H is incalculable for complex_list,
    # as the number of hapax legomena is equal to the number of total types
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        _ = complex_ngrams.honores_h

    # Normalized entropy should be lower for more repetitive sequences
    assert complex_ngrams.mean_entropy > simple_ngrams.mean_entropy

    # Mean productivity should be higher for more diverse sequences
    assert complex_ngrams.mean_productivity > simple_ngrams.mean_productivity


if __name__ == "__main__":
    test_mtype_tokenizer()
    test_mtype_encodings()
    test_ngram_counts()
