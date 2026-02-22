"""Export a Score to PDF format using Partitura + LilyPond."""

from pathlib import Path

from amads.core.basics import Score
from amads.io.pt_export import partitura_export
from amads.io.xml_lilypond_pdf import (
    lilypond_path_help,
    lilypond_to_pdf,
    musicxml_to_lilypond,
)


def partitura_xml_pdf_export(
    score: Score,
    filename: Path | str,
    show: bool = False,
    lilypond: bool = False,
    display: bool = False,
) -> None:
    """Save a Score to a file in PDF format using Partitura and LilyPond.

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
    filename : Path | str
        The name or path of the file to save the LilyPond or PDF data. Must be
        provided if `display` is False, and must end if `.ly` if `lilypond`
        is True, or `.pdf` if `lilypond` is False. If `display` is True,
        filename is optional and names the .pdf file to be written. In all
        cases, a LilyPond (.ly) file is written, either to `filename` or to
        a temporary directory when `display` is True or `lilypond` is False.
    show : bool, optional
        If True, print the partitura score structure for debugging.
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
    ly_path: Path
    pdf_path: Path | None
    xml_path: Path | None
    ly_path, pdf_path, xml_path = lilypond_path_help(
        filename, lilypond, display, True
    )

    # xml_path is not None here because lilypond_path_help had xml=True
    partitura_export(score, xml_path, "musicxml", show)  # type: ignore
    musicxml_to_lilypond(xml_path, ly_path)  # type: ignore
    if lilypond:
        return
    # pdf_path is not None here because lilypond is False
    lilypond_to_pdf(ly_path, pdf_path, display)  # type: ignore
