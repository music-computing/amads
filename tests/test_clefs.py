from amads.core.basics import Clef
from amads.io.readscore import read_score
from amads.music import example

_expected_clefs = [
    "treble",
    "treble8va",
    "treble15va",
    "treble8vb",
    "alto",
    "tenor",
    "bass",
    "bass8va",
    "bass8vb",
    "treble8vb",
    "treble",
    "french_violin",
    "soprano",
    "mezzosoprano",
    "constructed",
    "cbaritone",
    "bass15va",
    "bass15vb",
    "fbaritone",
    "subbass",
    "treble",
    "soprano",
    "alto",
    "tenor",
    "soprano",
    "alto",
    "treble",
]


def test_read_clefs():
    xml_file = example.fullpath("musicxml/clefs.musicxml")
    assert xml_file is not None
    score = read_score(xml_file, show=False)
    # score.show()
    clefs = score.list_all(Clef)
    for i, (expected, clef) in enumerate(zip(_expected_clefs, clefs)):
        assert expected == clef.clef, f"error in clef {i}"  # type: ignore
    clef = clefs[14]
    info = clef.get("clef_info")
    assert info[0] == "C", "bad constructed symbol"
    assert info[1] == 4, "bad constructed line"
    assert info[2] == -1, "bad constructed octave"
