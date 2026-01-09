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
        The name of the preferred MIDI writer. Can be "music21", "partitura", or "pretty_midi".

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
            "Invalid MIDI writer. Choose 'music21', 'partitura', or 'pretty_midi'."
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
            print(
                f"In writescore: importing partitura-based {file_type}"
                " writer."
            )
            if file_type == "midi":
                from amads.io.pt_midi_export import partitura_midi_export

                return partitura_midi_export
            else:
                from amads.io.pt_xml_export import partitura_xml_export

                return partitura_xml_export
        elif preferred_writer == "pretty_midi":
            print(
                f"In writescore: importing pretty_midi-based {file_type}"
                " writer."
            )
            from amads.io.pm_midi_export import pretty_midi_midi_export

            if file_type == "midi":
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

    <small>**Author**: Roger B. Dannenberg</small>
    """
    export_xml_fn = _check_for_subsystem("xml")
    if export_xml_fn is not None:
        export_xml_fn(score, filename, show)
    else:
        raise Exception(
            "Could not find a MusicXML export function. "
            "Preferred subsystem is" + str(preferred_xml_writer)
        )


def export_midi(
    score: Score,
    filename: str,
    show: bool = False,
) -> None:
    """Use Partitura or music21 or pretty_midi to export a Standard MIDI file.

    <small>**Author**: Roger B. Dannenberg</small>
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
    filename : str
        the path (relative or absolute) to the music file

    flatten : bool
        the returned score will be flat (Score, Parts, Notes)

    collapse: bool
        if collapse and flatten, the parts will be merged into one

    show : bool
        print a text representation of the data

    format: string
        one of 'xml', 'midi', 'kern', 'mei'
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
