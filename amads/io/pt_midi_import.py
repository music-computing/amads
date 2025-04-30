import partitura as pt

from ..core.basics import Score
from .pt_xml_import import partitura_convert_part

# plan: multiple passes over iter_all()
# for each part: add the part to a Concurrence
#      1st pass: get staff numbers from notes, extract measures, get div/qtr
#           create a Concurrence of staves if more than one,
#           create measures in each staff
#      2nd pass (A): get notes, rests, insert parameters into lists
#      2nd pass (B): build Note and Rest objects, insert into Measures
#      2nd pass (C): set ties attribute of Notes ?


def partitura_midi_import(filename, show=False):
    """User Partitura to import a MIDI file."""
    ptscore = pt.load_score_midi(filename)
    if show:
        for ptpart in ptscore:
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        partitura_convert_part(ptpart, score)
    return score
