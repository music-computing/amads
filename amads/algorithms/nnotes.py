"""
Provides the `nnotes` function

Original doc: github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 78.
"""

from amads.core.basics import Note, Score


def nnotes(score: Score, merge_ties: bool = True) -> int:
    """
    Returns the number of notes in a musical score.

    This is an implementation of the nnotes function in Matlab MIDItoolbox.

    Parameters
    ----------
    score : Score
        The musical score to analyze

    merge_ties : bool
        Count tied sequences of notes as a single note. Default is True.


    Returns
    -------
    int
        The number of notes in the score

    Examples
    --------
    >>> from amads.music import example
    >>> from amads.io.readscore import read_score
    >>> import contextlib
    >>> # Load example score while suppressing output:
    >>> with contextlib.redirect_stdout(None):
    ...     score = read_score(example.fullpath("musicxml/ex3.xml"))
    >>> nnotes(score)
    1
    >>> nnotes(score, merge_ties=False)
    2
    """
    return sum(
        1 for _ in score.find_all(Note, include_tied_to_notes=not merge_ties)
    )
