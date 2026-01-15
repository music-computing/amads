"""functions for file output"""

__author__ = "Roger B. Dannenberg"

import pathlib
from typing import Callable, Optional

from amads.core.basics import Score

# preferred_midi_writer is the subsystem to use for MIDI files.
# It can be "music21", "partitura", or "pretty_midi".
preferred_midi_writer = "pretty_midi"

# preferred_xml_writer is the subsystem to use for MusicXML files.
preferred_xml_writer = "music21"


def set_preferred_midi_writer(writer: str) -> str:
    """Set the preferred MIDI writer. Returns the previous writer
    preference so you can restore it if desired.

    Parameters
    ----------
    writer : str
        The name of the preferred MIDI writer. Can be "music21" or "pretty_midi".

    Returns
    -------
    str
        The previous name of the preferred MIDI writer.
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
    """Set the preferred XML writer. Returns the previous writer
    preference so you can restore it if desired.

    Parameters
    ----------
    writer : str
        The name of the preferred XML writer. Can be "music21" or "partitura".
    """
    global preferred_xml_writer
    previous_writer = preferred_xml_writer
    if writer in ["music21", "partitura"]:
        preferred_xml_writer = writer
    else:
        raise ValueError("Invalid XML writer. Choose 'music21' or 'partitura'.")
    return previous_writer


def _check_for_subsystem(
    file_type: str,
) -> Optional[Callable[[Score, str, bool], None]]:
    """Check if the preferred reader is available.

    Parameters
    ----------
    file_type : str
        The type of file to write, either 'midi' or 'xml'.

    Returns
    -------
    export_fn: functions for exporting MIDI or XML file
    """
    preferred_writer = (
        preferred_midi_writer if file_type == "midi" else preferred_xml_writer
    )
    try:
        if preferred_writer == "music21":
            print(f"In writescore: importing music21-based {file_type} writer.")
            if file_type == "midi":
                from amads.io.m21_midi_export import music21_midi_export

                return music21_midi_export
            else:
                from amads.io.m21_xml_export import music21_xml_export

                return music21_xml_export
        elif preferred_writer == "partitura":
            if file_type == "xml":
                print(
                    f"In writescore: importing partitura-based {file_type}"
                    " writer."
                )
                from amads.io.pt_xml_export import partitura_xml_export

                return partitura_xml_export
            else:  # Partitura can write a subset of MIDI using Performed.Part,
                # but not tempo changes or key signatures. A score can
                # represent these things but not MIDI velocity.
                raise Exception("Partitura does not support midi export.")
        elif preferred_writer == "pretty_midi":
            if file_type == "midi":
                print(
                    f"In writescore: importing pretty_midi-based {file_type}"
                    " writer."
                )
                from amads.io.pm_midi_export import pretty_midi_midi_export

                return pretty_midi_midi_export
            else:
                raise Exception("PrettyMIDI does not support XML export.")
    except Exception as e:
        print(f"Error importing {preferred_writer} for {file_type} files: {e}")
    return None


def export_xml(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Use Partitura or music21 to export a MusicXML file.

    Partitura does not seem to support per-staff key signatures,
    so key signatures from AMADS are simply added to Partitura
    parts. When there are multiple staffs, there could be
    duplicate key signatures (to be tested).

    <small>**Author**: Roger B. Dannenberg</small>
    """
    export_xml_fn = _check_for_subsystem("xml")
    if export_xml_fn is not None:
        export_xml_fn(score, filename, show)
    else:
        raise Exception(
            "Could not find a MusicXML export function. "
            "Preferred subsystem is " + str(preferred_xml_writer)
        )


def export_midi(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Use music21 or pretty_midi to export a Standard MIDI file.

    <small>**Author**: Roger B. Dannenberg</small>

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

    Pretty MIDI also requires an instrument name. If the AMADS Part
    `instrument` attribute is `None`, then `"Unknown"` is used. The
    Pretty MIDI reader will convert `"Unknown"` back to `None`.
    """
    export_midi_fn = _check_for_subsystem("midi")
    if export_midi_fn is not None:
        export_midi_fn(score, filename, show)
    else:
        raise Exception(
            "Could not find a MIDI file export function. "
            "Preferred subsystem is " + str(preferred_midi_writer)
        )


def write_score(
    score: Score,
    filename: str,
    show: bool = False,
    format=None,
) -> None:
    """Write a file with the given format, 'xml', 'midi', 'kern', 'mei'.

    If format is None (default), the format is based on the filename
    extension, which can be 'xml', 'mid', 'midi', 'smf', 'kern', or 'mei'

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    score : Score
        the score to write
    filename : str
        the path (relative or absolute) to the music file
    show : bool
        print a text representation of the data
    format: string
        one of 'xml', 'midi', 'kern', 'mei'

    Note
    ----
    See individual export methods, e.g. midi_export, xml_export, etc.,
    for details on how they handle various features like instrument,
    MIDI metadata, etc.
    """
    if format is None:
        ext = pathlib.Path(filename).suffix
        if ext == ".xml":
            format = "xml"
        elif ext == ".mid" or ext == ".midi" or ext == ".smf":
            format = "midi"
        elif ext == ".kern":
            format = "kern"
        elif ext == ".mei":
            format = "mei"
    if format == "xml":
        return export_xml(score, filename, show)
    elif format == "midi":
        return export_midi(score, filename, show)
    elif format == "kern":
        raise Exception("Kern format output not implemented")
    elif format == "mei":
        raise Exception("MEI format output not implemented")
    else:
        raise Exception(str(format) + " format specification is unknown")


"""
A list of supported file extensions for score reading.
"""
valid_score_extensions = [
    ".xml",
    ".musicxml",
    ".mid",
    ".midi",
    ".smf",
    ".kern",
    ".mei",
]
