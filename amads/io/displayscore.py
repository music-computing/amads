"""functions for score display"""

__author__ = "Roger B. Dannenberg"

import shutil
import subprocess
import sys
import tempfile

from amads.core.basics import Score
from amads.io.pianoroll import pianoroll
from amads.io.writescore import _write_or_display_score, write_score

# This module, writescore, is regarded as a singleton class with
# the following attributes:

preferred_display_method: str = "pdf"  # method to display music


def set_preferred_display_method(method: str) -> str:
    """Set a (new) preferred display method.

    Returns the previous preference. The current preference is stored
    in `amads.io.writer.preferred_display_method

    Parameters
    ----------
    method : str
        The name of the preferred method. Can be "pdf", "musescore" or
        "pianoroll". Note that if the method is "pdf", then
        `io.writescore.preferred_pdf_writer` is used to create a PDF to display.

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
    if method in ["pdf", "musescore", "pianoroll"]:
        preferred_display_method = method
    else:
        raise ValueError(
            "Invalid method. Choose 'pdf', 'musescore', or 'pianoroll'."
        )
    return previous_display_method


def display_score(score: Score, show: bool = False) -> None:
    """Display a score.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        the score to write
    show : bool
        show text representation of converted score for debugging
    """
    if preferred_display_method == "pdf":
        _write_or_display_score(score, None, show, "pdf", display=True)
    elif preferred_display_method == "pianoroll":
        pianoroll(score)  # Note that 'show' for pianoroll invokes plt.show(),
        # which is different from display_score's 'show' argument, which prints
        # a text representation of the score upon conversion. However,
        # pianoroll does not *do* conversion, so our 'show' argument is not
        # relevant here. pianoroll's 'show' argument is set to True by default.
    elif preferred_display_method == "musescore":
        with tempfile.NamedTemporaryFile(
            prefix="amads_display_", suffix=".musicxml", delete=False
        ) as tmp_file:
            xml_path = tmp_file.name

        write_score(score, xml_path, show, "musicxml")

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
