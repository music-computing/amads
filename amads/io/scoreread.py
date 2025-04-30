"""scoreread.py -- file input"""

__author__ = "Roger B. Dannenberg"

import pathlib

from amads.core.basics import Score

preferred_reader = "music21"  # default readers


def _check_alternate_subsystem() -> bool:
    """Check if the alternate reader is available. If so, install it.

    Returns:
    bool: True if a reader is available, False otherwise.
    """
    global preferred_reader
    original_reader = preferred_reader
    alternate_reader = "partitura" if preferred_reader == "music21" else "music21"
    print(f"In scoreread: {original_reader} is preferred reader,", "but not available.")
    print(f"Attepting to use {alternate_reader} instead.")
    preferred_reader = alternate_reader
    if _check_for_subsystem(_try_alternate=False):
        print(f"{preferred_reader} is available, using it instead.")
        return True
    else:
        print(f"{preferred_reader} is not available either.")
        preferred_reader = original_reader
        return False


def _check_for_subsystem(_try_alternate: bool = True) -> bool:
    """Check if the preferred reader is available. If so, install it.
    If not, try the alternate reader if _try_alternate is True.

    Returns:
    midi_import, xml_import: functions for importing MIDI and XML files
    """
    if preferred_reader == "music21":
        try:
            print("In scoreread: importing for music21")
            from amads.io.m21_midi_import import music21_midi_import
            from amads.io.m21_xml_import import music21_xml_import

            return music21_midi_import, music21_xml_import
        except ImportError:
            return _check_alternate_subsystem()
    elif preferred_reader == "partitura":
        try:
            from amads.io.pt_midi_import import partitura_midi_import
            from amads.io.pt_xml_import import partitura_xml_import

            return partitura_midi_import, partitura_xml_import
        except ImportError:
            return _check_alternate_subsystem()


def amads_xml_import(filename, show: bool = False) -> Score:
    """Use Partitura or music21 to import a MusicXML file."""
    _, xml_import = _check_for_subsystem()
    if xml_import is not None:
        return xml_import(filename, show)
    else:
        raise Exception(
            "Could not find a MusicXML import function. "
            + "Preferred subsystem is"
            + str(preferred_reader)
        )


def amads_midi_import(filename, show=False):
    """Use Partitura or music21 to import a Standard MIDI file."""
    midi_import, _ = _check_for_subsystem()
    if midi_import is not None:
        return midi_import(filename, show)
    else:
        raise Exception(
            "Could not find a MIDI file import function. "
            + "Preferred subsystem is "
            + str(preferred_reader)
        )


def score_read(filename, show=False, format=None):
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
        return amads_xml_import(filename, show)
    elif format == "midi":
        return amads_midi_import(filename, show)
    elif format == "kern":
        raise Exception("Kern format input not implemented")
    elif format == "mei":
        raise Exception("MEI format input not implemented")
    else:
        raise Exception(str(format) + " format specification is unknown")


def score_read_extensions():
    """
    Returns a list of supported file extensions for score reading.

    Returns:
    list of str: file extensions for score files. Not all are supported.
    """
    return [".xml", ".musicxml", ".mid", ".midi", ".smf", ".kern", ".mei"]
