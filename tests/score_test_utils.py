from collections.abc import Iterator

from amads.core.basics import Score


def get_annotation_values_iterator(
    annotated_score: Score, type: any, annotation_str: str
) -> Iterator:
    """
    Helper function to obtain annotation values in the sequence the elements
    appear in find_all.
    Useful utility that appears numerous times because we annotate individual
    elements when processing certain funcions.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze.
    type : any
        Type of object annotated within the score
    annotation_str : str
        Label that was used to annotate all the notes in the score.

    Returns
    -------
    Iterator
        Iterator of values that was annotated under the label.
    """
    return (
        elem.get(annotation_str, None)
        for elem in annotated_score.find_all(type)
    )
