"""Functions for music data input."""

__author__ = "Roger B. Dannenberg"

import pathlib
import tempfile
import urllib.request
import warnings
from typing import Callable, Optional

from amads.core.basics import Score

# This module, readscore, is regarded as a singleton class with
# the following attributes:

preferred_midi_reader: str = "pretty_midi"  # subsystem for MIDI file input
preferred_xml_reader: str = "music21"  # subsystem for MusicXML input
reader_warning_level: str = "default"  # controls verbocity of warnings
#     from input processing
_last_used_reader: Optional[Callable] = None  # See last_used_reader()

valid_score_extensions = [  # valid file extensions for score files
    ".xml",
    ".musicxml",
    ".mxl",
    ".mid",
    ".midi",
    ".smf",
    ".kern",
    ".krn",
    ".mei",
]


def set_preferred_midi_reader(reader: str) -> str:
    """
    Set a (new) preferred MIDI reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_midi_reader`.

    Parameters
    ----------
    reader : str
        The name of the preferred MIDI reader. Can be "music21" or "pretty_midi".

    Returns
    -------
    str
        The previous name of the preferred MIDI reader.

    Raises
    ------
    ValueError
        If an invalid reader is provided.
    """
    global preferred_midi_reader
    allowed = ["music21", "pretty_midi"]
    if reader not in allowed:
        raise ValueError(f"Invalid MIDI reader. Must be one of {allowed}")

    previous = preferred_midi_reader
    preferred_midi_reader = reader
    return previous


def set_preferred_xml_reader(reader: str) -> str:
    """
    Set a (new) preferred XML reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_xml_reader`.

    Parameters
    ----------
    reader : str
        The name of the preferred XML reader. Can be "music21" or "partitura".

    Returns
    -------
    str
        The previous name of the preferred XML reader.

    Raises
    ------
    ValueError
        If an invalid reader is provided.
    """
    global preferred_xml_reader
    allowed = ["music21", "partitura"]
    if reader not in allowed:
        raise ValueError(f"Invalid XML reader. Must be one of {allowed}")

    previous = preferred_xml_reader
    preferred_xml_reader = reader
    return previous


def set_reader_warning_level(level: str) -> str:
    """
    Set the warning level for `readscore` functions.

    The translation from music data files to AMADS is not always well-defined
    and may involve intermediate representations using Music21, Partitura or
    others. Usually, warnings are produced when there is possible data loss or
    ambiguity, but these can be more annoying than informative. The warning
    level can be controlled using this function, which applies to all file
    formats.

    The current warning level is stored in
    `amads.io.reader.reader_warning_level`.

    Parameters
    ----------
    level : str
        The warning level to set.
        Options are "none", "low", "default", "high".

        - "none" will suppress all warnings during `read_score()`
          and also suppresses notice of reader subsystem and file name.
        - "low" will print one notice if there are any warnings.
        - "default" will obey environment settings to control warnings.
        - "high" will print all warnings during `read_score()`, overriding
            environment settings.

    Returns
    -------
    str
        Previous warning level.

    Raises
    ------
    ValueError
        If an invalid warning level is provided.
    """
    global reader_warning_level
    allowed = ["none", "low", "default", "high"]
    if level not in allowed:
        raise ValueError(f"Invalid warning level. Must be one of {allowed}")

    previous = reader_warning_level
    reader_warning_level = level
    return previous


def _check_for_subsystem(
    file_type: str,
) -> Optional[Callable[[str, bool, bool, bool, bool], Score]]:
    """
    Check if the preferred reader is available.

    We support:
    `music21` for midi and xml,
    `partitura` for xml,
    and
    `PrettyMIDI` for midi.

    Partitura has basic MIDI import functionality, but is unsupported here
    because when it reads in a score it has no MIDI velocity
    and when it reads in a performance it has no tempo track, key signature, etc.

    Parameters
    ----------
    file_type : str
        The type of file to read, either 'midi' or 'xml'.

    Returns
    -------
    Optional[Callable]
        The import function if available.
    """
    reader = (
        preferred_midi_reader if file_type == "midi" else preferred_xml_reader
    )

    try:
        if reader == "music21":
            if file_type == "midi":
                from amads.io.m21_midi_import import music21_midi_import

                return music21_midi_import
            else:
                from amads.io.m21_xml_import import music21_xml_import

                return music21_xml_import
        elif reader == "partitura":
            if file_type == "xml":
                from amads.io.pt_xml_import import partitura_xml_import

                return partitura_xml_import
            else:
                raise ImportError(
                    "Partitura MIDI import not currently supported"
                )
        elif reader == "pretty_midi":
            if file_type == "midi":
                from amads.io.pm_midi_import import pretty_midi_midi_import

                return pretty_midi_midi_import
            else:
                raise ImportError("PrettyMIDI does not support XML import")
    except ImportError as e:
        print(f"Error importing {reader} for {file_type} files: {e}")
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
    global _last_used_reader
    import_xml_fn = _check_for_subsystem("xml")
    if import_xml_fn is not None:
        _last_used_reader = import_xml_fn
        if reader_warning_level != "none":
            print(
                f"Reading {filename} using MusicXML reader "
                f"file={import_xml_fn.__name__}."
            )
        return import_xml_fn(
            filename, flatten, collapse, show, group_by_instrument
        )
    else:
        raise Exception(
            "Could not find a MusicXML import function. "
            f"Preferred subsystem is {preferred_xml_reader}"
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
    global _last_used_reader
    import_midi_fn = _check_for_subsystem("midi")
    if import_midi_fn is not None:
        _last_used_reader = import_midi_fn
        if reader_warning_level != "none":
            print(
                f"Reading {filename} using MIDI reader "
                f"{import_midi_fn.__name__}."
            )
        return import_midi_fn(
            filename, flatten, collapse, show, group_by_instrument
        )
    else:
        raise Exception(
            "Could not find a MIDI file import function. "
            f"Preferred subsystem is {preferred_midi_reader}"
        )


def read_score(
    filename: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    format: Optional[str] = None,
    group_by_instrument: bool = True,
) -> Score:
    """Read a file with the given format, `'xml'`, `'midi'`, `'kern'`, `'mei'`.

    If format is None (default), the format is based on the filename
    extension, which can be `'xml'`, `'mid'`, `'midi'`, `'smf'`, `'kern'`,
    or `'mei'`. (Valid extensions are in
    `amads.io.readscore.valid_score_extensions`.)

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    filename : str
        The path (relative or absolute) to the music file.
        Can also be an URL.
    flatten : bool
        The returned score will be flat (Score, Parts, Notes).
    collapse: bool
        If collapse and flatten, the parts will be merged into one.
    show : bool
        Print a text representation of the data.
    format: string
        One from among limited standard options (e.g.,
        `'xml'`, `'midi'`, `'kern'`, `'mei'`)
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
        The imported score

    Raises
    ------
    ValueError
        If the format is unknown or not implemented.
    """
    if filename.startswith("http") or "://" in filename:
        with tempfile.NamedTemporaryFile(
            suffix=pathlib.Path(filename).suffix or ".tmp", delete=False
        ) as tmp_file:
            urllib.request.urlretrieve(filename, tmp_file.name)
            filename = tmp_file.name

    if format is None:
        ext = pathlib.Path(filename).suffix.lower()
        if ext in [".xml", ".musicxml", ".mxl"]:
            format = "xml"
        elif ext in [".mid", ".midi", ".smf"]:
            format = "midi"
        elif ext == ".kern":
            format = "kern"
        elif ext == ".mei":
            format = "mei"
        else:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Valid extensions: {valid_score_extensions}"
            )

    # File format handling
    with warnings.catch_warnings(record=True) as w:
        if reader_warning_level == "none":
            warnings.simplefilter("ignore")
        else:
            warnings.simplefilter("always")

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
            raise ValueError(
                "Kern format input not implemented yet. "
                "Consider using the `kernr` package."
            )
        elif format == "mei":
            raise ValueError(
                "MEI format input not implemented yet. "
                "Consider using the `mei` package."
            )
        else:
            raise ValueError(f"{format} format specification is unknown")

        # Warning handling
        if reader_warning_level == "low":
            if len(w) > 0:
                print(
                    f"Warning: {len(w)} warnings were generated in "
                    f"read_score({filename}).\n"
                    "  Use amads.io.readscore.set_reader_warning_level() "
                    "for more details."
                )
        else:  # "none", "default", or "high"
            for warning in w:
                print(
                    f"{warning.filename}:{warning.lineno}: "
                    f"{warning.category.__name__}: {warning.message}"
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
    if _last_used_reader is not None:
        return _last_used_reader.__name__
    return None
