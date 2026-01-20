"""functions for file input"""

__author__ = "Roger B. Dannenberg"

import pathlib
import warnings
from typing import Callable, Optional

from amads.core.basics import Score

# preferred_midi_reader is the subsystem to use for MIDI files.
# It can be "music21", "partitura", or "pretty_midi".
preferred_midi_reader = "pretty_midi"

# preferred_xml_reader is the subsystem to use for MusicXML files.
preferred_xml_reader = "music21"

# remember the actual reader used in the last call to readscore()
last_used_reader_fn = None

# warning levels for read_score
_reader_warning_level = "default"


def set_preferred_midi_reader(reader: str) -> str:
    """Set the preferred MIDI reader. Returns the previous reader
    preference so you can restore it if desired.

    Parameters
    ----------
    reader : str
        The name of the preferred MIDI reader. Can be "music21", "partitura", or "pretty_midi".

    Returns
    -------
    str
        The previous name of the preferred MIDI reader.
    """
    global preferred_midi_reader
    previous_reader = preferred_midi_reader
    if reader in ["music21", "partitura", "pretty_midi"]:
        preferred_midi_reader = reader
    else:
        raise ValueError(
            "Invalid MIDI reader. Choose 'music21', 'partitura', or 'pretty_midi'."
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


def set_reader_warning_level(level: str) -> str:
    """Set the warning level for readscore functions.

        - "none" - will suppress all warnings during read_score().
            Also suppresses notice of reader subsystem and file name.
        - "low" - will show print one notice if there are any warnings.
        - "default" - will obey environment settings to control warnings.
        - "high" - will print all warnings during read_score(), overriding
            environment settings.

    Parameters
    ----------
    level : str
        The warning level to set. Can be "none", "low", "default", "high".

    Returns
    -------
    str
        Previous warning level.

    Raises
    -------
    ValueError
        If an invalid warning level is provided.
    """
    global _reader_warning_level
    previous_level = _reader_warning_level
    if level in ["none", "low", "default", "high"]:
        _reader_warning_level = level
    else:
        raise ValueError(
            "Invalid warning level. Choose 'none', 'low', 'default', or 'high'."
        )
    return previous_level


def _check_for_subsystem(
    file_type: str,
) -> Optional[Callable[[str, bool, bool, bool, bool], Score]]:
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
            if file_type == "midi":
                from amads.io.m21_midi_import import music21_midi_import

                return music21_midi_import
            else:
                from amads.io.m21_xml_import import music21_xml_import

                return music21_xml_import
        elif preferred_reader == "partitura":
            if file_type == "xml":
                from amads.io.pt_xml_import import partitura_xml_import

                return partitura_xml_import
            else:  # Partitura can read into a score, but it has no MIDI
                # velocity, or it can read into a performance, but it
                # has no tempo track, key signature, etc.
                raise ImportError("Partitura does not support midi import.")
        elif preferred_reader == "pretty_midi":
            if file_type == "midi":
                from amads.io.pm_midi_import import pretty_midi_midi_import

                return pretty_midi_midi_import
            else:
                raise ImportError("PrettyMIDI does not support XML import.")
    except ImportError as e:
        print(f"Error importing {preferred_reader} for {file_type} files: {e}")
    return None


def import_xml(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """Use Partitura or music21 to import a MusicXML file.

    In Music21, the first measure may be a partial measure containing
    an anacrusis (“pickup”). This is somewhat ambiguous and does not
    translate well to MIDI which is less expressive than MusicXML.

    Therefore, if the first measure read with Music21 is not a full
    measure, a rest is inserted and the remainder is shifted to
    form a full measure according to its time signature.

    <small>**Author**: Roger B. Dannenberg</small>
    """
    import_xml_fn = _check_for_subsystem("xml")
    if import_xml_fn is not None:
        global last_used_reader_fn
        last_used_reader_fn = import_xml_fn
        if _reader_warning_level != "none":
            print(
                f"Reading {filename} using MusicXML reader"
                f" file={import_xml_fn.__name__}."
            )
        return import_xml_fn(
            filename, flatten, collapse, show, group_by_instrument
        )
    else:
        raise Exception(
            "Could not find a MusicXML import function. "
            "Preferred subsystem is" + str(preferred_xml_reader)
        )


def import_midi(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """Use music21 or pretty_midi to import a Standard MIDI file.

    <small>**Author**: Roger B. Dannenberg</small>

    Notes
    -----
    Each Standard MIDI File track corresponds to a Staff when
    creating a full AMADS Score. Everything is combined into one
    part when `flatten` and `collapse` are specified.

    AMADS assumes that instruments (midi program numbers) are fixed
    for each Staff (or Part in flat scores), and MIDI channels are
    not represented. The use of program change messages within a
    track to change the program are ignored, but may generate warnings.

    In general, AMADS instrument name corresponds to the MIDI track
    name, and MIDI program numbers are stored as `"midi_program"`
    in the `info` attribute of the Staff or Part corresponding to
    the track.

    MIDI files do not have a Part/Staff structure, but you can
    write multiple tracks with the same name. Both the `"music21"`
    and `"pretty_midi"` readers will group tracks with matching
    names as Staffs in a single Part. This may result in an
    unexpected Part/Staff hierarchy if tracks are not named or
    if tracks are named something like "Piano-Treble" and
    "Piano-Bass", which would produce two Parts as different
    instruments as opposed to one Part with two Staffs.

    Unless `flatten` or `collapse`, the MIDI file time signature
    information will be used to form Measures with Staffs, and
    Notes will be broken where they cross measure boundaries and
    then tied.  The default time signature is 4/4.

    Pretty MIDI Import Notes
    ------------------------
    If there is no program change in a file, the `"pretty_midi"`
    reader will use 0, and 0 will be stored as `"midi_program"`
    in the Part or Staff's `info` (see
    [get][amads.core.basics.Event.get] and
    [set][amads.core.basics.Event.set]).

    If there is no track name, the `Part.instrument` is derived
    from the track program number (defaults to zero).

    If the MIDI file track name is `"Unknown"`, the `Part.instrument`
    is set to None. This is because when the `"pretty_midi"` writer
    writes a part where `Part.instrument is None`, the name `"Unknown"`
    is used instead. Therefore, the reader will recreate the AMADS
    Part where `Part.instrument is None`.

    Pretty MIDI will not insert any KeySignature unless key signature
    meta-events are found.

    Music21 MIDI Import Notes
    -------------------------
    Music21 may infer a Clef and KeySignature even though MIDI
    does not even have a meta-event for clefs, and even if the
    MIDI file has no key signature meta-event.
    """
    import_midi_fn = _check_for_subsystem("midi")
    if import_midi_fn is not None:
        global last_used_reader_fn
        last_used_reader_fn = import_midi_fn
        if _reader_warning_level != "none":
            print(
                f"Reading {filename} using MIDI reader"
                f" {import_midi_fn.__name__}."
            )
        return import_midi_fn(
            filename, flatten, collapse, show, group_by_instrument
        )
    else:
        raise Exception(
            "Could not find a MIDI file import function. "
            "Preferred subsystem is " + str(preferred_midi_reader)
        )


def read_score(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    format=None,
    group_by_instrument: bool = True,
) -> Score:
    """Read a file with the given format, 'xml', 'midi', 'kern', 'mei'.

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
    group_by_instrument : bool
        If True (default), when the underlying reader (e.g. for "pretty_midi",
        "music21" or "partitura") reads Parts with the same instrument, their
        content will be grouped into a single part. This means that if
        `flatten`, then parts with the same instrument will be merged into a
        single part. If `flatten` is False, then the staffs of parts with the
        same instrument will be grouped within a single part.
        If `group_by_instrument` is False, the parts read in by the underlying
        reader will be preserved as separate parts. `group_by_instrument` is
        True by default so that when reading Piano scores with separate treble
        and bass staffs, the resulting AMADS Score will generally have a single
        Piano part with two staffs. A score for Piano and Violin will generally
        have two parts, one for Piano and one for Violin, as opposed to three
        parts (Piano-Treble, Piano-Bass, Violin). On the other hand, a score for
        two Violins might be represented a one part with two staffs by default,
        but setting `group_by_instrument` to False will more likely keep the
        two Violin parts separate. Unfortunately, exact behavior depends on the
        underlying reader, MIDI track names, and/or MusicXML structure and
        naming.

    Returns
    -------
    Score
        the imported score

    Raises
    ------
    ValueError
        If the format is unknown or not implemented.

    Note
    ----
    See individual readers and writers for details on how they handle
    various features like instrument, MIDI metadata, etc.
    """
    with warnings.catch_warnings(record=True) as w:
        if _reader_warning_level == "none":
            warnings.simplefilter("ignore")
        else:
            warnings.simplefilter("always")

        if format is None:
            ext = pathlib.Path(filename).suffix
            if ext == ".xml" or ext == ".musicxml" or ext == ".mxl":
                format = "xml"
            elif ext == ".mid" or ext == ".midi" or ext == ".smf":
                format = "midi"
            elif ext == ".kern":
                format = "kern"
            elif ext == ".mei":
                format = "mei"
        if format == "xml":
            score = import_xml(
                filename,
                flatten,
                collapse,
                show,
                group_by_instrument=group_by_instrument,
            )
        elif format == "midi":
            score = import_midi(
                filename,
                flatten,
                collapse,
                show,
                group_by_instrument=group_by_instrument,
            )
        elif format == "kern":
            raise ValueError("Kern format input not implemented")
        elif format == "mei":
            raise ValueError("MEI format input not implemented")
        else:
            raise ValueError(str(format) + " format specification is unknown")

        if _reader_warning_level == "low":
            if len(w) > 0:
                print(
                    f"Warning: {len(w)} warnings were generated in"
                    f" read_score({filename})."
                )
                print(
                    "  Use amads.io.readscore.set_reader_warning_level()"
                    " for more details."
                )
        else:  # "none", "default", or "high"
            for warning in w:
                print(
                    f"{warning.filename}:{warning.lineno}:"
                    f" {warning.category.__name__}: {warning.message}"
                )
        return score


def last_used_reader() -> Optional[str]:
    """Return the name of the last used reader function.

    Returns
    -------
    Optional[str]
        The name of the actual function used in the last call to `read_score`,
        or None if no reader has been used yet.
    """
    if last_used_reader_fn is not None:
        return last_used_reader_fn.__name__
    return None


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
