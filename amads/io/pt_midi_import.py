import partitura as pt
from pathlib import Path

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


def partitura_midi_import(filename, ptprint=False):
    """Use Partitura to import a MIDI file.
    
    Parameters
    ----------
    filename : str or Path
        Path to the MIDI file to import
    ptprint : bool, optional
        If True, print the Partitura score representation, by default False
        
    Returns
    -------
    Score
        The imported score
        
    Raises
    ------
    FileNotFoundError
        If the MIDI file does not exist
    """
    if not Path(filename).exists():
        raise FileNotFoundError(f"MIDI file not found: {filename}")
        
    ptscore = pt.load_score_midi(filename)
    if ptprint:
        for ptpart in ptscore:
            print(ptpart.pretty())
    score = Score()
    for ptpart in ptscore.parts:
        score.append(partitura_convert_part(ptpart, score))
    return score
