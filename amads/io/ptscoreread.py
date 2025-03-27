# ptscoreread.py -- file input
#
import pathlib

from amads.io.pt_midi_import import partitura_midi_import
from amads.io.pt_xml_import import partitura_xml_import


def score_read(filename, pprint=False, format=None):
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
        return partitura_xml_import(filename, ptprint=pprint)
    elif format == "midi":
        return partitura_midi_import(filename, ptprint=pprint)
    elif format == "kern":
        raise Exception("Kern format input using Partitura not implemented")
    elif format == "mei":
        raise Exception("MEI format input using Partitura not implemented")
    else:
        raise Exception(str(format) + " format specification is unknown")


def score_read_extensions():
    """
    Returns a list of supported file extensions for score reading.

    Returns:
    list of str: Supported file extensions.
    """
    return [".xml", ".musicxml", ".mid", ".midi", ".smf", ".kern", ".mei"]
