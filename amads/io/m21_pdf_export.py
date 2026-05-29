"""Export a Score to PDF format using music21 + LilyPond."""

from pathlib import Path
from typing import Optional, cast

from music21 import stream

from amads.core.basics import Score
from amads.io import writescore
from amads.io.m21_export import _score_to_music21, music21_export
from amads.io.xml_lilypond_pdf import _lilipond_to_pdf, _musicxml_to_lilypond


def _music21_to_lilypond(
    m21score: stream.Score, ly_path: Optional[Path | str]
) -> None:
    """Convert a music21 score to LilyPond and write to a .ly file."""
    ly_path = writescore._path_help(ly_path, ".ly")  # type: ignore
    ly_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore
    m21score.write("lilypond", fp=str(ly_path))

    text = ly_path.read_text(encoding="utf-8")  # type: ignore (ly_path is Path)
    text = text.replace("\\RemoveEmptyStaffContext\n", "")
    text = text.replace(
        "    \\override VerticalAxisGroup #'remove-first = ##t\n", ""
    )
    ly_path.write_text(text, encoding="utf-8")  # type: ignore (ly_path is Path)


def music21_pdf_export(
    score: Score, filename: str | Path, format: str, show: bool, is_temp: bool
) -> None:
    """Save a Score to a file in lilypond or PDF format using music21.

    Temporary files are created as needed for intermediate LilyPond and PDF
    output. Runs lilypond to create PDF if format is "pdf".

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str | Path
        The name of the file to save the LilyPond or PDF data.
    format : str
        The format to export. Must be "pdf" or "lilypond".
    show : bool, optional
        If True, print the music21 score structure for debugging
        with the label "Music21 score structure"
    is_temp: bool
        If True, we can make temp file names by changing filename suffix.

    Raises
    ------
    ValueError
        If `filename` does not have the expected extension.
    """
    m21score = _score_to_music21(score, show, filename)

    if format == "lilypond":
        ly_path = writescore._path_help(filename, ".ly", is_temp=is_temp)
    elif format == "pdf":
        result = writescore._path_help(
            filename, [".pdf", ".PDF"], ".ly", is_temp=is_temp
        )
        assert isinstance(result, tuple)
        (pdf_path, ly_path) = result

    _music21_to_lilypond(m21score, ly_path)  # type: ignore (ly_path is set)
    if format == "pdf":
        _lilipond_to_pdf(ly_path, pdf_path)  # type: ignore (pdf_path is set)


def music21_xml_pdf_export(
    score: Score, filename: str | Path, format: str, show: bool, is_temp: bool
) -> None:
    """Write Score to a file using music21, musicxml2ly and LilyPond.

    Supports formats "pdf" and "lilypond".

    Temporary files are created as needed for intermediate XML, LilyPond,
    and PDF output.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str | Path
        The name of the file to save the LilyPond or PDF data.
    format : str
        The format to export. Must be "pdf" or "lilypond".
    show : bool, optional
        If True, print the music21 score structure for debugging.
    is_temp: bool
        If True, we can make temp file names by changing filename suffix.

    Raises
    ------
    ValueError
        If `filename`  does not have the expected extension, of if `format` is
        not "pdf" or "lilypond".
    """
    _score_to_music21(score, show, filename)
    xml_path = None

    if format == "lilypond":
        result = writescore._path_help(
            filename, ".ly", ".musicxml", is_temp=is_temp
        )
        assert isinstance(result, tuple)
        (ly_path, xml_path) = result
    elif format == "pdf":
        result = writescore._path_help(
            filename, [".pdf", ".PDF"], ".musicxml", is_temp=is_temp
        )
        assert isinstance(result, tuple)
        (pdf_path, ly_path) = result
        xml_path = ly_path.with_suffix(".musicxml")

    music21_export(score, cast(Path, xml_path), "musicxml", show, is_temp)
    _musicxml_to_lilypond(xml_path, ly_path, True)  # type: ignore

    if format == "pdf":
        _lilipond_to_pdf(ly_path, pdf_path)  # type: ignore (ly_path is set)
