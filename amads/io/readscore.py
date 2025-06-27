"""readscore.py -- file input"""

__author__ = "Roger B. Dannenberg"

import pathlib
from typing import Callable, Optional

from amads.core.basics import Score

# preferred_midi_reader is the subsystem to use for MIDI files.
# It can be "music21", "partitura", or "prettymidi".
preferred_midi_reader = "prettymidi"

# preferred_xml_reader is the subsystem to use for MusicXML files.
preferred_xml_reader = "music21"


def set_preferred_midi_reader(reader: str) -> str:
    """Set the preferred MIDI reader. Returns the previous reader
    preference so you can restore it if desired.

    Parameters
    ----------
    reader : str
        The name of the preferred MIDI reader. Can be "music21", "partitura", or "prettymidi".

    Returns
    -------
    str
        The previous name of the preferred MIDI reader.
    """
    global preferred_midi_reader
    previous_reader = preferred_midi_reader
    if reader in ["music21", "partitura", "prettymidi"]:
        preferred_midi_reader = reader
    else:
        raise ValueError(
            "Invalid MIDI reader. Choose 'music21', 'partitura', or 'prettymidi'."
        )
    return previous_reader


def set_preferred_xml_reader(reader: str) -> str:
    """Set the preferred XML reader. Returns the previous reader
    preference so you can restore it if desired.

    Parameters
    ----------
    reader : str
        The name of the preferred XML reader. Can be "music21" or "partitura".
    """
    global preferred_xml_reader
    previous_reader = preferred_xml_reader
    if reader in ["music21", "partitura"]:
        preferred_xml_reader = reader
    else:
        raise ValueError("Invalid XML reader. Choose 'music21' or 'partitura'.")
    return previous_reader


def _check_for_subsystem(file_type: str) -> Optional[Callable[[str, bool], Score]]:
    """Check if the preferred reader is available.

    Parameters
    ----------
    file_type : str
        The type of file to read, either 'midi' or 'xml'.

    Returns
    -------
    import_fn: functions for importing MIDI or XML file
    """
    preferred_reader = (
        preferred_midi_reader if file_type == "midi" else preferred_xml_reader
    )
    try:
        if preferred_reader == "music21":
            print(f"In readscore: importing music21-based {file_type} reader.")
            if file_type == "midi":
                from amads.io.m21_midi_import import music21_midi_import

                return music21_midi_import
            else:
                from amads.io.m21_xml_import import music21_xml_import

                return music21_xml_import
        elif preferred_reader == "partitura":
            print(f"In readscore: importing partitura-based {file_type}" " reader.")
            if file_type == "midi":
                from amads.io.pt_midi_import import partitura_midi_import

                return partitura_midi_import
            else:
                from amads.io.pt_xml_import import partitura_xml_import

                return partitura_xml_import
        elif preferred_reader == "prettymidi":
            print(f"In readscore: importing prettymidi-based {file_type}" " reader.")
            from amads.io.pm_midi_import import pretty_midi_midi_import

            if file_type == "midi":
                return pretty_midi_midi_import
            else:
                raise ImportError("PrettyMIDI does not support XML import.")
    except ImportError as e:
        print(f"Error importing {preferred_reader} for {file_type} files: {e}")
    return None


def import_xml(filename, show: bool = False) -> Score:
    """Use Partitura or music21 to import a MusicXML file."""
    import_xml_fn = _check_for_subsystem("xml")
    if import_xml_fn is not None:
        return import_xml_fn(filename, show)
    else:
        raise Exception(
            "Could not find a MusicXML import function. "
            "Preferred subsystem is" + str(preferred_xml_reader)
        )


def import_midi(
    filename: str, flatten: bool = False, collapse: bool = False, show: bool = False
):
    """Use Partitura or music21 or pretty_midi to import
    a Standard MIDI file.
    """
    import_midi_fn = _check_for_subsystem("midi")
    if import_midi_fn is not None:
        return import_midi_fn(filename, flatten=flatten, collapse=collapse, show=show)
    else:
        raise Exception(
            "Could not find a MIDI file import function. "
            "Preferred subsystem is " + str(preferred_midi_reader)
        )


def read_score(filename, show=False, format=None):
    """read a file with the given format, 'xml', 'midi', 'kern', 'mei'.
    If format is None (default), the format is based on the filename
    extension, which can be 'xml', 'mid', 'midi', 'smf', 'kern', or 'mei'
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
        return import_xml(filename, show)
    elif format == "midi":
        return import_midi(filename, show)
    elif format == "kern":
        raise Exception("Kern format input not implemented")
    elif format == "mei":
        raise Exception("MEI format input not implemented")
    else:
        raise Exception(str(format) + " format specification is unknown")


"""
A list of supported file extensions for score reading.
"""
valid_score_extensions = [".xml", ".musicxml", ".mid", ".midi", ".smf", ".kern", ".mei"]
