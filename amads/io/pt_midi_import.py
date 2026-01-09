import partitura as pt

from amads.core.basics import Note, Score
from amads.io.pt_xml_import import partitura_convert_part

# Details:
#    Partitura does not retain velocity (dynamic) in scores, but scores
# have structure. So we read midi files TWICE! First, we read using
# load_score_midi() and use pt_xml_import's partitura_convert_part
# to build a Score. Then we use load_performance() to get MIDI notes.
# We match the performance notes to score notes and assign dynamics.
#
#    If flatten, then we can avoid load_score_midi -- future work


def partitura_midi_import(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
) -> Score:
    """User Partitura to import a MIDI file."""
    ptscore = pt.load_score_midi(filename)
    if show:
        print(f"Partitura score structure from {filename}:")
        print(ptscore.__class__)
        print("------- here are the parts -------")
        for ptpart in ptscore:
            print(ptpart.__class__)
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        partitura_convert_part(ptpart, score, rnd=False)

    ptperf = pt.load_performance(filename)
    if show:
        print(f"Partitura performance structure from {filename}:")
        print(ptperf.__class__, "num_tracks", ptperf.num_tracks)
        print("------- here are the parts -------")
        for ptpart in ptperf.performedparts:
            print(ptpart.__class__)
            print(ptpart.note_array())

    # move MIDI velocities from ptparts to AMADS Parts:
    for part, ptpart in zip(score.content, ptperf.performedparts):
        for note, ptnote in zip(part.find_all(Note), ptpart.note_array()):
            assert note.key_num == ptnote[4], (
                "pitch mismatch: " f"{note} vs {ptnote}"
            )
            note.dynamic = ptnote[5]

    # this might be optimized by building a flat score to start with:
    if flatten or collapse:
        score = score.flatten(collapse=collapse)
    return score
