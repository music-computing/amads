"""Functions for score display

    <small>**Author**: Roger B. Dannenberg</small>
"""

__author__ = "Roger B. Dannenberg"

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from importlib.resources import files

from amads.core.basics import Score
from amads.io.pianoroll import pianoroll
from amads.io.readscore import read_score
from amads.io.writescore import _write_or_display_score, write_score

# This module, writescore, is regarded as a singleton class with
# the following attributes:

preferred_display_method: str = "pdf"  # method to display music


def suppress_external_open() -> bool:
    return os.environ.get("AMADS_NO_OPEN") == "1" or (
        "PYTEST_CURRENT_TEST" in os.environ
    )


def set_preferred_display_method(method: str) -> str:
    """Set a (new) preferred display method.

    Returns the previous preference. The current preference is stored
    in `amads.io.writer.preferred_display_method`

    Parameters
    ----------
    method : str
        The name of the preferred method. Can be "pdf", "musescore", "OSMD"
        (Open Sheet Music Display) or "pianoroll". Note that if the method
        is "pdf", then `io.writescore.preferred_pdf_writer` is used to create
        a PDF to display.

    Returns
    -------
    str
        The previous name of the preferred method.

    Raises
    ------
    ValueError
        If an invalid method is provided.
    """
    global preferred_display_method
    previous_display_method = preferred_display_method
    if method in ["pdf", "musescore", "OSMD", "pianoroll"]:
        preferred_display_method = method
    else:
        raise ValueError(
            "Invalid method. Choose 'pdf', 'musescore', 'OSMD', or 'pianoroll'."
        )
    return previous_display_method


def _get_osmd_js() -> str:
    return files("amads.js").joinpath("osmd.min.js").read_text(encoding="utf-8")


def _load_mxl(path: str) -> str:
    """
    Extract the MusicXML content from a compressed .mxl file.

    An .mxl ZIP archive contains a META-INF/container.xml that identifies
    the root MusicXML file. Fall back to the first .xml/.musicxml entry
    if container.xml is absent.
    """
    with zipfile.ZipFile(path, "r") as zf:
        # Try the standard MXL manifest first
        if "META-INF/container.xml" in zf.namelist():
            container = zf.read("META-INF/container.xml").decode("utf-8")
            # The rootfile element's full-path attribute names the XML file
            import xml.etree.ElementTree as ET

            root = ET.fromstring(container)
            ns = {"mc": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//mc:rootfile", ns)
            if rootfile is not None:
                xml_filename = rootfile.attrib["full-path"]
                return zf.read(xml_filename).decode("utf-8")

        # Fallback: first .xml or .musicxml entry that isn't the manifest
        for name in zf.namelist():
            if name.startswith("META-INF"):
                continue
            if name.endswith(".xml") or name.endswith(".musicxml"):
                return zf.read(name).decode("utf-8")

    raise ValueError(f"No MusicXML content found in {path}")


def display_file(file: str) -> None:
    """Display a score from a file path.

    Parameters
    ----------
    file : str
        the file (must be MIDI or MusicXML) to display.

    Raises
    ------
    RunTimeError
        If `file` does not end with ".mid", ".midi", ".xml", ".musicxml"
        or ".mxl".
    """
    if file.endswith(".mid") or file.endswith(".midi"):
        score = read_score(file)
        pianoroll(score)
    elif (
        file.endswith(".xml")
        or file.endswith(".musicxml")
        or file.endswith(".mxl")
    ):
        _display_musicxml_file(file)
    else:
        raise RuntimeError(
            f"Unsupported file extension for display_file: {file}"
        )


def display_score(score: Score, show: bool = False) -> None:
    """Display a score.

    AMADS supports several display methods. "pdf" (default) uses the
    preferred MusicXML writer (defaults to Music21) to write an XML file.
    Then, Lilypond (which must be installed) is run to create a pdf file.
    The pdf file is then opened using Python's `webbrowser.open`, which
    may in fact open the pdf with Preview on MacOS.

    "pianoroll" will make a pianoroll display directly from the score
    and plot it, showing the plot.

    "musescore" will make a MusicXML file using the preferred MusicXML
    writer and open the file with MuseScore, which must be installed.

    "OSMD" will  make a MusicXML file using the preferred MusicXML
    writer. It then constructs a web page consisting of the MusicXML
    file (as a Javascript text string) and OSMD (the Open Sheet
    Music Display library which runs in the browser to render the
    MusicXML). The constructed HTML file is opened in a browser.

    Parameters
    ----------
    score : Score
        the score to write
    show : bool
        show text representation of converted score for debugging.
    """
    if preferred_display_method == "pdf":
        _write_or_display_score(score, None, show, "pdf", display=True)
    elif preferred_display_method == "pianoroll":
        pianoroll(score)  # Note that 'show' for pianoroll invokes plt.show(),
        # which is different from display_score's 'show' argument, which prints
        # a text representation of the score upon conversion. However,
        # pianoroll does not *do* conversion, so our 'show' argument is not
        # relevant here. pianoroll's 'show' argument is set to True by default.
    elif (
        preferred_display_method == "musescore"
        or preferred_display_method == "OSMD"
    ):
        with tempfile.NamedTemporaryFile(
            prefix="amads_display_", suffix=".musicxml", delete=False
        ) as tmp_file:
            xml_path = tmp_file.name

        write_score(score, xml_path, show, "musicxml")

        if suppress_external_open():
            print(f"score display suppressed during tests; wrote {xml_path}")
            return
        _display_musicxml_file(xml_path)
    else:
        raise RuntimeError(
            f"Unsupported display method: {preferred_display_method}"
        )


def _display_musicxml_file(xml_path: str) -> None:
    """
    Construct a complete static web page with embedded OSMD and
    the generated MusicXML, then open it in the default browser
    """
    if preferred_display_method == "musescore":
        musescore_exe = (
            shutil.which("musescore")
            or shutil.which("musescore4")
            or shutil.which("musescore3")
            or shutil.which("mscore")
        )
        if musescore_exe:
            subprocess.Popen([musescore_exe, xml_path])
            return

        if sys.platform == "darwin":
            for app_name in [
                "MuseScore Studio",
                "MuseScore 4",
                "MuseScore 3",
                "MuseScore",
            ]:
                result = subprocess.run(
                    ["open", "-a", app_name, xml_path],
                    capture_output=True,
                    check=False,
                    text=True,
                )
                if result.returncode == 0:
                    return

            subprocess.Popen(["open", xml_path])
            return

        raise RuntimeError(
            "Could not find MuseScore executable. Ensure MuseScore is "
            "installed and on PATH."
        )

    else:  # preferred_display_method == "OSMD"
        osmd_js = _get_osmd_js()
        path = os.path.abspath(xml_path)
        if zipfile.is_zipfile(path):
            musicxml_content = _load_mxl(path)
        else:
            with open(xml_path) as f:
                musicxml_content = f.read()
        html_content = f"""<!DOCTYPE html>
    <html lang="en">
<head>
<meta charset="UTF-8">
<title>OSMD Display</title>
</head>
<body>
<script>{osmd_js}</script>
<div id="osmd-container"></div>
<script>
    // Initialize OSMD with the MusicXML content
    const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(
                            "osmd-container", {{ autoResize: true }});
    osmd.load({repr(musicxml_content)}).then(() => osmd.render());
</script>
</body>
</html>"""
        with tempfile.NamedTemporaryFile(
            prefix="amads_osmd_display_", suffix=".html", delete=False
        ) as tmp_html_file:
            tmp_html_file.write(html_content.encode("utf-8"))
            html_path = tmp_html_file.name

        if suppress_external_open():
            print(f"OSMD display suppressed during tests; wrote {html_path}")
            return

        if sys.platform == "darwin":
            subprocess.Popen(["open", html_path])
        elif sys.platform == "win32":
            os.startfile(html_path)
        else:
            subprocess.Popen(["xdg-open", html_path])
