"""functions for file output"""

__author__ = "Roger B. Dannenberg"

import pathlib
import warnings
from typing import Callable, Optional

from amads.core.basics import Score

# This module, writescore, is regarded as a singleton class with
# the following attributes:

preferred_midi_writer: str = "pretty_midi"  # subsystem for MIDI file output
preferred_xml_writer: str = "music21"  # subsystem for MusicXML file output
preferred_kern_writer: str = "pretty_midi"  # subsystem for Kern file output
preferred_mei_writer: str = "pretty_midi"  # subsystem for Kern file output
preferred_pdf_writer: str = "music21-lilypond"  # subsystems for PDF file output
writer_warning_level: str = "default"  # controls verbocity of warnings
#     from output processing
_last_used_writer: Optional[Callable] = None  # See last_used_writer()

# mappings from suffix to format:
_suffix_to_format = {
    ".xml": "musicxml",
    ".musicxml": "musicxml",
    ".mxl": "musicxml",
    ".mid": "midi",
    ".midi": "midi",
    ".smf": "midi",
    ".krn": "kern",
    ".kern": "kern",
    ".mei": "mei",
    ".pdf": "pdf",
    ".ly": "lilypond",
}

# A list of supported file extensions for score writing.
valid_score_extensions = _suffix_to_format.keys()

allowed_subsystems = {
    "midi": ["music21", "pretty_midi"],
    "musicxml": ["music21", "partitura"],
    "kern": ["music21"],
    "mei": ["music21"],
    "pdf": [
        "music21-lilypond",
        "music21-xml-lilypond",
        "partitura-xml-lilypond",
    ],
    "lilypond": [
        "music21-lilypond",
        "music21-xml-lilypond",
        "partitura-xml-lilypond",
    ],
}

# mapping from preference strings to subsystem callables
_subsystem_map = {
    "music21": ("amads.io.m21_export", "music21_export"),
    "pretty_midi": ("amads.io.pm_midi_export", "pretty_midi_export"),
    "partitura": ("amads.io.pt_export", "partitura_export"),
    "music21-lilypond": ("amads.io.m21_pdf_export", "music21_pdf_export"),
    "music21-xml-lilypond": (
        "amads.io.m21_pdf_export",
        "music21_xml_pdf_export",
    ),
    "partitura-xml-lilypond": (
        "amads.io.pt_pdf_export",
        "partitura_xml_pdf_export",
    ),
}


def set_preferred_midi_writer(writer: str) -> str:
    """Set a (new) preferred MIDI writer.

    Returns the previous writer preference. The current preference is stored
    in `amads.io.writer.preferred_midi_writer`.

    Parameters
    ----------
    writer : str
        The name of the preferred MIDI writer. Can be "music21" or "pretty_midi".

    Returns
    -------
    str
        The previous name of the preferred MIDI writer.

    Raises
    ------
    ValueError
        If an invalid writer is provided.

    """
    global preferred_midi_writer
    previous_writer = preferred_midi_writer
    if writer in ["music21", "partitura", "pretty_midi"]:
        preferred_midi_writer = writer
    else:
        raise ValueError(
            "Invalid MIDI writer. Choose 'music21', 'partitura', or "
            "'pretty_midi'."
        )
    return previous_writer


def set_preferred_xml_writer(writer: str) -> str:
    """
    Set a (new) preferred XML writer.

    Returns the previous writer preference. The current preference is stored
    in `amads.io.writer.preferred_xml_writer`.

    Parameters
    ----------
    writer : str
        The name of the preferred XML writer. Can be "music21" or "partitura".

    Returns
    -------
    str
        The previous name of the preferred XML writer.

    Raises
    ------
    ValueError
        If an invalid writer is provided.
    """
    global preferred_xml_writer
    previous_writer = preferred_xml_writer
    if writer in allowed_subsystems["musicxml"]:
        preferred_xml_writer = writer
    else:
        raise ValueError("Invalid XML writer. Choose 'music21' or 'partitura'.")
    return previous_writer


def set_preferred_kern_writer(writer: str) -> str:
    """
    Set a (new) preferred Kern writer.

    Returns the previous writer preference. The current preference is stored
    in `amads.io.writer.preferred_kern_writer`.

    Parameters
    ----------
    writer : str
        The name of the preferred Kern writer. Can be "music21".

    Returns
    -------
    str
        The previous name of the preferred Kern writer.

    Raises
    ------
    ValueError
        If an invalid writer is provided.
    """
    global preferred_kern_writer
    previous_writer = preferred_kern_writer
    if writer in allowed_subsystems["kern"]:
        preferred_kern_writer = writer
    else:
        raise ValueError("Invalid Kern writer. Choose 'music21'.")
    return previous_writer


def set_preferred_mei_writer(writer: str) -> str:
    """
    Set a (new) preferred MEI writer.

    Returns the previous writer preference. The current preference is stored
    in `amads.io.writer.preferred_mei_writer`.

    Parameters
    ----------
    writer : str
        The name of the preferred MEI writer. Can be "music21".

    Returns
    -------
    str
        The previous name of the preferred MEI writer.

    Raises
    ------
    ValueError
        If an invalid writer is provided.
    """
    global preferred_mei_writer
    previous_writer = preferred_mei_writer
    if writer in allowed_subsystems["mei"]:
        preferred_mei_writer = writer
    else:
        raise ValueError("Invalid MEI writer. Choose 'music21'.")
    return previous_writer


def set_preferred_pdf_writer(writer: str) -> str:
    """
    Set a (new) preferred PDF writer.

    Returns the previous writer preference. The current preference is stored
    in `amads.io.writescore.preferred_pdf_writer`. Preferences are:
    - "music21-lilypond" - use music21 to create a LilyPond file, then use
      LilyPond to create a PDF.
    - "music21-xml-lilypond" - use music21 to create a MusicXML file, then run
      the program musicxml2ly to convert XML to LilyPond, then run LilyPond to
      create a PDF.
    - "partitura-xml-lilypond" - use partitura to create a MusicXML file, then
      run the program musicxml2ly to convert XML to LilyPond, then run LilyPond
      to create a PDF.


    Parameters
    ----------
    writer : str
        The name of the preferred PDF writer. Can be "music21-lilypond",
        "music21-xml-lilypond", or "partitura-xml-lilypond".

    Returns
    -------
    str
        The previous name of the preferred PDF writer.

    Raises
    ------
    ValueError
        If an invalid writer is provided.
    """
    global preferred_pdf_writer
    previous_writer = preferred_pdf_writer
    if writer in allowed_subsystems["pdf"]:
        preferred_pdf_writer = writer
    else:
        raise ValueError(
            "Invalid PDF writer. Choose " f"{allowed_subsystems['pdf']}."
        )
    return previous_writer


def set_writer_warning_level(level: str) -> str:
    """
    Set the warning level for writescore functions.

    The translation from AMADS to music data files is not always well-defined
    and may involve intermediate representations using Music21, Partitura or
    others. Usually, warnings are produced when there is possible data loss or
    ambiguity, but these can be more annoying than informative. The warning
    level can be controlled using this function, which applies to all file
    formats.

    The current warning level is stored in
    `amads.io.writer.writer_warning_level`.

    Parameters
    ----------
    level : str
        The warning level to set. Can be "none", "low", "default", "high".

        - "none" - will suppress all warnings during write_score().
        - "low" - will show print one notice if there are any warnings.
        - "default" - will obey environment settings to control warnings.
        - "high" - will print all warnings during write_score(), overriding
            environment settings.

    Returns
    -------
    str
        Previous warning level.

    Raises
    -------
    ValueError
        If an invalid warning level is provided.
    """
    global writer_warning_level
    previous_level = writer_warning_level
    if level in ["none", "low", "default", "high"]:
        writer_warning_level = level
    else:
        raise ValueError(
            "Invalid warning level. Choose 'none', 'low', 'default', or 'high'."
        )
    return previous_level


def _check_for_subsystem(
    format: str,
) -> tuple[
    Optional[Callable[[Score, Optional[str], Optional[str], bool, bool], None]],
    Optional[str],
]:
    """Check if the preferred subsystem is available.

    Parameters
    ----------
    format : str
        The format of the file to write, either 'midi', 'musicxml', or 'pdf'.

    Returns
    -------
    tuple[Optional[Callable], Optional[str]]
        The export function if available, None otherwise, and the name of
        the subsystem used.
    """
    preferred_writer = {
        "midi": preferred_midi_writer,
        "musicxml": preferred_xml_writer,
        "kern": preferred_midi_writer,
        "mei": preferred_midi_writer,
        "pdf": preferred_pdf_writer,
    }.get(format)

    if not preferred_writer:
        return None, None

    try:
        if (
            preferred_writer not in _subsystem_map
            or preferred_writer not in allowed_subsystems[format]
        ):
            raise ValueError(
                f"Preferred writer '{preferred_writer}' not supported for "
                f"{format} export."
            )

        module_name, func_name = _subsystem_map[preferred_writer]
        module = __import__(module_name, fromlist=[func_name])
        # note that the type signature of func_name has an extra `display``
        # when format is "pdf", so if you call it with a `display` argument,
        # type checking will complain:
        return getattr(module, func_name), preferred_writer
    except Exception as e:
        print(f"Error importing {preferred_writer} for {format} files: {e}")
    return None, preferred_writer


def _export_score(
    score: Score,
    filename: Optional[str],
    format: str,
    show: bool = False,
    display: bool = False,
) -> None:
    """Use Partitura or music21 to export a MusicXML file.

    <small>**Author**: Roger B. Dannenberg</small>
    """
    global _last_used_writer

    export_fn, subsystem = _check_for_subsystem(format)
    if export_fn is not None:
        _last_used_writer = export_fn
        if writer_warning_level != "none":
            print(
                f"Exporting {filename} using {format} writer"
                f" {export_fn.__name__} from subsystem {subsystem}."
            )
        export_fn(score, filename, format, show, display)
    else:
        raise Exception(
            f"Could not find an export function for format {format}. "
            "Preferred subsystem is " + str(subsystem)
        )


def write_score(
    score: Score,
    filename: str,
    show: bool = False,
    format: Optional[str] = None,
) -> None:
    """Write a file with the given format.

    If format is None (default), the format is based on the filename
    extension, which can be one of `writescore.valid_score_extensions`
    ('xml', 'musicxml', 'mxl', 'mid', 'midi', 'smf', 'krn', 'kern',
    'mei', 'pdf', or 'ly').

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        the score to write
    filename : Optional[str]
        the path (relative or absolute) to the music file. Optional only
        when display is True, but for display, you should call `display_score`
        instead.
    show : bool
        print a text representation of the data
    format : Optional[string]
        one of `'musicxml'`, `'midi'`, `'kern'`, `'mei'`, `'pdf'`, `'lilypond'`.
        Defaults to the format implied by `filename`.

    Raises
    ------
    ValueError
        if format is unknown

    Notes
    -----
    AMADS assumes that instruments (midi program numbers) are fixed
    for each Staff (or Part in flat scores), and MIDI channels are
    not represented. This corresponds to some DAWs such as LogicPro,
    which represents channels but ignores them when tracks are
    synthesized in software by a single instrument. The MIDI program
    is stored as info (see [get][amads.core.basics.Event.get] and
    [set][amads.core.basics.Event.set]) under key `"midi_program"`
    on the Staff, or if there is no Staff or no `"midi_program"` on
    the Staff, under key `"midi_program"` on the Part.

    Parts also have an `instrument` attribute, which is stored as
    the MIDI track name. (Therefore, if a Part has two Staffs, there
    will be two tracks with the same name.)  If there is no MIDI
    program for the track, the `'pretty_midi'` writer will use
    `pretty_midi.instrument_name_to_program` to determine a program
    number since a program number is required. (As opposed to Standard
    MIDI Files, which need not have any MIDI program message at all.)
    If `pretty_midi.instrument_name_to_program` fails, the program is
    set to 0 (“Acoustic Grand Piano”).

    Partitura does not seem to support per-staff key signatures,
    so key signatures from AMADS are simply added to Partitura
    parts. When there are multiple staffs, there could be
    duplicate key signatures (to be tested).

    Pretty MIDI also requires an instrument name. If the AMADS Part
    `instrument` attribute is `None`, then `"Unknown"` is used. The
    Pretty MIDI reader will convert `"Unknown"` back to `None`.

    """
    _write_or_display_score(score, filename, show, format, False)


def _write_or_display_score(
    score: Score,
    filename: Optional[str],
    show: bool = False,
    format: Optional[str] = None,
    display: bool = False,
) -> None:
    """Write or display a Score.

    If format is None (default), the format is based on the filename
    extension, which can be one of `writescore.valid_score_extensions`
    ('xml', 'musicxml', 'mxl', 'mid', 'midi', 'smf', 'krn', 'kern',
    'mei', 'pdf', or 'ly').

    If display is True, the goal is to display the file, so the
    filename is optional, and a temporary file will be used if needed.

    display is suppressed by setting AMADS_NO_OPEN=1 in the environment,
    which is used in testing with pytest so the user does not have to close
    a bunch of windows opened by demos that are run as part of testing.

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        the score to write
    filename : Optional[str]
        the path (relative or absolute) to the music file. Optional only
        when display is True, but for display, you should call `display_score`
        instead.
    show : bool
        print a text representation of the data
    format : Optional[string]
        one of 'musicxml', 'midi', 'kern', 'mei', 'pdf', 'lilypond'.
        Defaults to the format implied by `filename`.
    display : bool
        If True and format is 'pdf', the created PDF file is displayed.

    Raises
    ------
    ValueError
        if format is unknown
    """

    if not display and not filename:
        raise ValueError("filename must be provided if display is False")
    if format is None and not filename:
        raise ValueError("format must be provided if filename is not provided")

    # Type checking complains about filename being possibly None, but we
    # check for that above, so we can ignore it here.
    if format is None and filename:
        ext = pathlib.Path(filename).suffix  # type: ignore
        format = _suffix_to_format.get(ext)
        if not format:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Valid extensions: {valid_score_extensions}"
            )
    elif format not in _suffix_to_format.values():
        raise ValueError(f"Unknown or unspecified format: {format}")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter(
            "ignore" if writer_warning_level == "none" else "always"
        )

        # here, we know format is valid, so ignore type checking:
        _export_score(score, filename, format, show, display)  # type: ignore

        # Warning handling
        if writer_warning_level == "low":
            if len(w) > 0:
                print(
                    f"Warning: {len(w)} warnings were generated in"
                    f" write_score({filename}). Use"
                    " amads.io.writescore.set_writer_warning_level() for"
                    " more details."
                )
        else:  # "none", "default", or "high"
            for warning in w:
                formatted = warnings.formatwarning(
                    warning.message,
                    warning.category,
                    warning.filename,
                    warning.lineno,
                )
                print(formatted, end="")
