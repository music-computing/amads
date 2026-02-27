"""Convert MusicXML to PDF format via LilyPond."""

import shutil
import subprocess
import tempfile
import webbrowser
from pathlib import Path

from amads.io.displayscore import suppress_external_open


def lilypond_path_help(
    filename: Path | str, lilypond: bool, display: bool, xml: bool
) -> tuple[Path, Path | None, Path | None]:
    """There are multiple messy ways to determine file names and paths.
    This helper function serves both music21_pdf_export and
    music21_xml_pdf_export.

    If `lilypond`, then ly_path will be filename; otherwise, ly_path
    will be a temp file.

    Parameters
    ----------
    filename : Path | str
        The filename for the pdf export.
    lilypond: bool
        True to retain the lilypond (.ly) file
    display: bool
        True if the pdf file will be displayed, meaning filename is optional.
    xml: bool
        True if we also need an xml file path
    """
    ly_path: Path | None = None
    pdf_path: Path | None = None
    xml_path: Path | None = None

    work_dir = None
    stem = "score"

    if not filename and not lilypond and not display:
        raise ValueError(
            "filename must be provided if lilypond and" " display are False"
        )
    elif filename:
        ext = Path(filename).suffix.lower()
        if lilypond:
            ly_path = Path(filename)
            if ext != ".ly":
                raise ValueError(
                    f"filename extension {ext} must be .ly when"
                    " lilypond is True"
                )
        else:
            pdf_path = Path(filename)
            if ext != ".pdf":
                raise ValueError(
                    f"filename extension {ext} must be .pdf when"
                    " lilypond is False"
                )

    if not ly_path:
        work_dir = Path(tempfile.mkdtemp(prefix="amads_lilypond_"))
        ly_path = work_dir / f"{stem}.ly"
    if not pdf_path and not lilypond:
        if not work_dir:
            work_dir = Path(tempfile.mkdtemp(prefix="amads_lilypond_"))
        pdf_path = work_dir / f"{stem}.pdf"
    if xml:
        if not work_dir:
            work_dir = Path(tempfile.mkdtemp(prefix="amads_lilypond_"))
        xml_path = work_dir / f"{stem}.musicxml"

    return (ly_path, pdf_path, xml_path)


def lilypond_to_pdf(
    ly_path: Path | str, pdf_path: Path | str, display: bool = False
) -> None:
    """Convert a Lilypond (.ly) file to PDF.

    Parameters
    ----------
    ly_path : Path | str
        The path to the LilyPond file.
    pdf_path : Path | str
        The path to the PDF file.
    display : bool, optional
        If True, open the generated PDF in the default viewer.

    Raises
    ------
    RuntimeError
        If LilyPond fails to convert the file.
    """

    # we have pdf_path ending in ".pdf" but lilypond will add ".pdf", so
    # remove the extension. Then run LilyPond to create the PDF.
    if not isinstance(ly_path, (str, Path)):
        raise ValueError(f"ly_path must be a string or Path, got {ly_path}.")
    if not isinstance(pdf_path, (str, Path)):
        raise ValueError(f"pdf_path must be a string or Path, got {pdf_path}.")
    pdf_path_obj = Path(pdf_path)
    output_base = pdf_path_obj.with_suffix("")
    command = ["lilypond", "-o", str(output_base), str(ly_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "LilyPond failed. If `lilypond` did not even start, ensure that\n"
            "`lilypond` is installed and on PATH.\n"
            "In VS Code: You may need to set the PATH in your settings.json,\n"
            "    although there are at least four separate settings related\n"
            "    to setting the PATH! A more direct approach is hard-code\n"
            "    PATH in .vscode/launch.json for the configuration(s) you are\n"
            '    using: "env": {"PATH": "path-to-lilypond:${env:PATH}"}\n'
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    if display:
        if suppress_external_open():
            print(f"PDF display suppressed during tests, wrote {pdf_path}.")
        else:
            webbrowser.open(pdf_path_obj.resolve().as_uri())  # type: ignore


def _add_measure_numbers_to_xml(
    xml_content: str, xml_path: Path | str, xml_temp_file: bool
) -> Path:
    """Add measure numbers to a MusicXML file if they are missing, because
    musicxml2ly requires measure numbers.

    Parameters
    ----------
    xml_content : str
        The content of the MusicXML file.
    xml_path : Path | str
        The path to the MusicXML file.
    xml_temp_file : bool
        If True, xml_path is a temporary file that can be overwritten with
        the modified content.

    Returns
    -------
    Path
        The path to the modified MusicXML file.
    """
    if not xml_temp_file:
        work_dir = Path(tempfile.mkdtemp(prefix="amads_lilypond_"))
        new_xml_path = work_dir / "score_with_measure_numbers.musicxml"
    else:
        new_xml_path = Path(xml_path)
    with open(new_xml_path, "w", encoding="utf-8") as f:
        measure_count = 0
        pos = 0
        next_part_loc = xml_content.find("<part", pos)
        if next_part_loc == -1:
            raise RuntimeError(f"No <part> tags found in {xml_path}.")
        while True:
            loc = xml_content.find("<measure", pos)
            if loc == -1:
                f.write(xml_content[pos:])
                break
            loc2 = xml_content.find(">", loc)
            if loc2 == -1:
                raise RuntimeError(
                    f"No closing '>' found in {xml_path} after <measure."
                )
            measure_tag = xml_content[loc : loc2 + 1]
            if loc > next_part_loc:
                measure_count = 0
                next_part_loc = xml_content.find("<part", loc)
                if next_part_loc == -1:
                    next_part_loc = len(xml_content) + 1
            if "number=" not in measure_tag:
                measure_count += 1
                new_measure_tag = (
                    measure_tag[:-1] + f' number="{measure_count}">'
                )
                f.write(xml_content[pos:loc] + new_measure_tag)
            else:
                f.write(xml_content[pos : loc2 + 1])
            pos = loc2 + 1
    return new_xml_path


def musicxml_to_lilypond(
    xml_path: Path | str, ly_path: Path | str, xml_temp_file=False
) -> None:
    """Convert a MusicXML file to a LilyPond file.

    Parameters
    ----------
    xml_path : Path | str
        The path to the MusicXML file.
    ly_path : Path | str
        The path to the LilyPond file.

    Raises
    ------
    RuntimeError
        If musicxml2ly fails to convert the file.
    """
    musicxml2ly = shutil.which("musicxml2ly")
    if not musicxml2ly:
        raise RuntimeError(
            "Could not find musicxml2ly. Ensure LilyPond is installed and "
            "musicxml2ly is on PATH.\n"
            "In VS Code: You may need to set the PATH in your settings.json,\n"
            "    although there are at least four separate settings related\n"
            "    to setting the PATH! A more direct approach is hard-code\n"
            "    PATH in .vscode/launch.json for the configuration(s) you are\n"
            '    using: "env": {"PATH":'
            ' "path-to-musicxml2ly:${env:PATH}"}\n'
        )

    # make sure xml measures have numbers, otherwise musicxml2ly will fail.
    # Partitura apparently omits measure numbers, which is a problem.
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    loc = xml_content.find("<measure")
    if loc == -1:
        raise RuntimeError(f"No <measure> tags found in {xml_path}.")
    loc2 = xml_content.find(">", loc)
    if loc2 == -1:
        raise RuntimeError(
            f"No closing '>' found in {xml_path} after <measure."
        )
    measure_tag = xml_content[loc : loc2 + 1]
    if "number=" not in measure_tag:
        xml_path = _add_measure_numbers_to_xml(
            xml_content, xml_path, xml_temp_file
        )

    # now xml_path is either the original xml_path (if it already had
    # measure numbers) or a new file was created with measure numbers.
    command = [musicxml2ly, "-o", str(ly_path), str(xml_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "musicxml2ly failed. Ensure LilyPond is installed and on PATH.\n"
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
