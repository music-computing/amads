def test_get_root_parncutt_1988():
    from amads.all import get_root_parncutt_1988

    chord = [0, 4, 7]
    root = get_root_parncutt_1988(chord)
    assert root == 0
