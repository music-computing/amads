from typing import cast

from music21 import converter
from music21.stream import Score as m21Score

from amads.core.basics import Score
from amads.io.m21_xml_import import music21_to_score


def music21_midi_import(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """Use music21 to import a MIDI file and convert it to a Score.

    Parameters
    ----------
    filename : str
        The path to the MIDI file.
    flatten : bool, optional
        If True, flatten the score structure.
    collapse : bool, optional
        If True and flatten is true, also collapse parts.
    show : bool, optional
        If True, print the music21 score structure for debugging.
    group_by_instrument: bool, optional
        If True, group parts by instrument name into staffs. Defaults to True.
        See `music21_to_score` for details.

    Returns
    -------
    Score
        The converted AMADS Score object.
    """
    # Load the MIDI file using music21
    m21score = converter.parse(
        filename, format="midi", forceSource=True, quantizePost=False
    )
    m21score = cast(m21Score, m21score)
    score = music21_to_score(
        m21score,
        flatten,
        collapse,
        show,
        filename,
        group_by_instrument=group_by_instrument,
    )
    return score
