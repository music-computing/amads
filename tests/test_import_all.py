def test_get_root_parncutt_1988():
    from amads.all import ParncuttRootAnalysis

    chord = [0, 4, 7]
    analysis = ParncuttRootAnalysis(chord)
    assert analysis.root == 0
