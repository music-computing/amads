"""Export a Score to MIDI format using music21."""

from amads.core.basics import Score
from amads.io.m21_xml_export import score_to_music21


def music21_midi_export(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Save a Score to a file in MIDI format using music21.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the MIDI data.
    show : bool, optional
        If True, print the music21 score structure for debugging.
    """
    m21score = score_to_music21(score, show, filename)
    m21score.write("midi", filename)
