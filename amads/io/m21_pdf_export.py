"""Export a Score to PDF format using music21 + LilyPond."""

from pathlib import Path

from music21 import stream

from amads.core.basics import Score
from amads.io.m21_export import music21_export, score_to_music21
from amads.io.xml_lilypond_pdf import (
    lilypond_path_help,
    lilypond_to_pdf,
    musicxml_to_lilypond,
)


def _write_lilypond_file(m21score: stream.Score, ly_path: Path) -> None:
    """Convert a music21 score to LilyPond and write to a .ly file."""
    ly_path.parent.mkdir(parents=True, exist_ok=True)
    m21score.write("lilypond", fp=str(ly_path))

    text = ly_path.read_text(encoding="utf-8")
    text = text.replace("\\RemoveEmptyStaffContext\n", "")
    text = text.replace(
        "    \\override VerticalAxisGroup #'remove-first = ##t\n", ""
    )
    ly_path.write_text(text, encoding="utf-8")


def music21_pdf_export(
    score: Score,
    filename: str,
    show: bool = False,
    lilypond: bool = False,
    display: bool = False,
) -> None:
    """Save a Score to a file in PDF format using music21 and LilyPond.

    There are three main modes of operation, controlled by the `lilypond`
    and `display` flags:

    - To save a PDF file without opening it, set `lilypond=False` and provide a
      `filename` ending in `.pdf`.
    - To save a LilyPond file without converting to PDF, set `lilypond=True`
      and provide a `filename` ending in `.ly`.
    - To save and display a PDF file, set `display=True` and *optionally*
      provide a `filename` ending in `.pdf`.

    Temporary files are created as needed for intermediate LilyPond and PDF
    output.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the LilyPond or PDF data. Must be
        provided if `display` is False, and must end if `.ly` if `lilypond`
        is True, or `.pdf` if `lilypond` is False. If `display` is True,
        filename is optional and names the .pdf file to be written. In all
        cases, a LilyPond (.ly) file is written, either to `filename` or to
        a temporary directory when `display` is True or `lilypond` is False.
    show : bool, optional
        If True, print the music21 score structure for debugging.
    lilypond : bool, optional
        If True, also save the intermediate LilyPond file rather than PDF.
    display : bool, optional
        If True, open the generated PDF in the default viewer.

    Raises
    ------
    ValueError
        If `filename` is not provided when `display` is False, or if
        `filename` extension is not the expected `.pdf` or `.ly`.
    """
    ly_path: Path | None = None
    pdf_path: Path | None = None
    ly_path, pdf_path, _ = lilypond_path_help(
        filename, lilypond, display, False
    )

    m21score = score_to_music21(score, show, filename)
    _write_lilypond_file(m21score, ly_path)
    if lilypond:
        return

    lilypond_to_pdf(ly_path, pdf_path, display)  # type: ignore


def music21_xml_pdf_export(
    score: Score,
    filename: str,
    show: bool = False,
    lilypond: bool = False,
    display: bool = False,
) -> None:
    """Write Score as PDF file using music21, musicxml2ly and LilyPond.

    There are three main modes of operation, controlled by the `lilypond`
    and `display` flags:

    - To save a PDF file without opening it, set `lilypond=False` and provide a
      `filename` ending in `.pdf`.
    - To save a LilyPond file without converting to PDF, set `lilypond=True`
      and provide a `filename` ending in `.ly`.
    - To save and display a PDF file, set `display=True` and *optionally*
      provide a `filename` ending in `.pdf`.

    Temporary files are created as needed for intermediate XML, LilyPond,
    and PDF output.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str
        The name of the file to save the LilyPond or PDF data. Must be
        provided if `display` is False, and must end if `.ly` if `lilypond`
        is True, or `.pdf` if `lilypond` is False. If `display` is True,
        filename is optional and names the .pdf file to be written. In all
        cases, a LilyPond (.ly) file is written, either to `filename` or to
        a temporary directory when `display` is True or `lilypond` is False.
    show : bool, optional
        If True, print the music21 score structure for debugging.
    lilypond : bool, optional
        If True, also save the intermediate LilyPond file rather than PDF.
    display : bool, optional
        If True, open the generated PDF in the default viewer.

    Raises
    ------
    ValueError
        If `filename` is not provided when `display` is False, or if
        `filename` extension is not the expected `.pdf` or `.ly`, or if
        lilypond2ly or lilypond executables are not found or fail.
    """
    ly_path: Path
    pdf_path: Path | None
    xml_path: Path | None
    ly_path, pdf_path, xml_path = lilypond_path_help(
        filename, lilypond, display, True
    )
    # xml_path is not None here
    music21_export(score, xml_path, "musicxml", show, display)  # type: ignore
    musicxml_to_lilypond(xml_path, ly_path)  # type: ignore (xml_path != None)
    if lilypond:
        return
    # pdf_path is not None here because lilypond is False
    lilypond_to_pdf(ly_path, pdf_path, display)  # type: ignore
