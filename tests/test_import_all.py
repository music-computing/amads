def test_root_parncutt_1988():
    from amads.all import root_parncutt_1988

    chord = [0, 4, 7]
    root = root_parncutt_1988(chord)
    assert root == 0
