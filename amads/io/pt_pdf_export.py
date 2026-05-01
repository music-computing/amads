"""Export a Score to PDF format using Partitura + LilyPond."""

from pathlib import Path

from amads.core.basics import Score
from amads.io import writescore
from amads.io.pt_export import _score_to_partitura, partitura_export
from amads.io.xml_lilypond_pdf import _lilipond_to_pdf, _musicxml_to_lilypond


def partitura_xml_pdf_export(
    score: Score, filename: str | Path, format: str, show: bool, is_temp: bool
) -> None:
    """Save a Score to a file in Lilypond or PDF format using Partitura.

    Temporary files are created as needed for intermediate XML, LilyPond,
    and PDF output.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        The Score to export.
    filename : str | Path
        Names the pdf or lilypond file to create.
    format : str
        The format to export. Must be "pdf" or "lilypond".
    show : bool, optional
        If True, print the partitura score structure for debugging
        with the label "Music21 score structure"
    is_temp: bool
        If True, we can make temp file names by changing filename suffix.

    Raises
    ------
    ValueError
        If `filename` extension is not the expected `.pdf` or `.ly`.
    """
    _score_to_partitura(score, show, filename)
    # Determine format from filename and check consistency:
    if not isinstance(filename, Path):
        filename = Path(filename)

    format = writescore._update_format_with_filename(format, filename)
    # we need a filename for musicxml:
    if format == "lilypond":
        ly_path = writescore._path_help(
            filename, ".ly", ".musicxml", is_temp  # type: ignore
        )
    else:  # format == "pdf"
        result = writescore._path_help(
            filename, [".pdf", ".PDF"], ".ly", is_temp
        )
        assert isinstance(result, tuple)
        pdf_path, ly_path = result

    result = writescore._path_help(None, ".musicxml", ".ly")
    assert isinstance(result, tuple)
    xml_path, ly_path = result
    partitura_export(score, xml_path, "musicxml", show, is_temp)
    _musicxml_to_lilypond(xml_path, ly_path, True)

    if format == "pdf":
        _lilipond_to_pdf(ly_path, pdf_path)  # type: ignore  (pdf_path is set)
