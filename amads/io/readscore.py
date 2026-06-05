"""Functions for music data input."""

__author__ = "Roger B. Dannenberg"

import tempfile
import urllib.request
import warnings
from pathlib import Path
from typing import Callable, Optional, cast

from amads.core.basics import Chord, Measure, Note, Rest, Score, Staff
from amads.io.writescore import _suffix_to_format

# This module, readscore, is regarded as a singleton class with
# the following attributes:

_default_midi_reader = "mido"
_default_xml_reader = "music21"
_default_kern_reader = "music21"
_default_mei_reader = "music21"

preferred_midi_reader: str = (
    _default_midi_reader  # subsystem for MIDI file input
)
preferred_xml_reader: str = _default_xml_reader  # subsystem for MusicXML input
preferred_kern_reader: str = _default_kern_reader  # subsystem for Kern input
preferred_mei_reader: str = _default_mei_reader  # subsystem for mei input
reader_warning_level: str = "default"  # controls verbocity of warnings
#     from input processing
_last_used_reader: Optional[Callable] = None  # See last_used_reader()

valid_score_extensions = list(_suffix_to_format.keys())
valid_score_extensions.remove(".pdf")
valid_score_extensions.remove(".ly")  # write-only extensions

allowed_subsystems = {
    "midi": ["music21", "pretty_midi", "mido"],
    "musicxml": ["music21", "partitura"],
    "kern": ["music21", "partitura"],
    "mei": ["music21", "partitura"],
}

# mapping from preference strings to subsystem callables
_subsystem_map = {
    "music21": ("amads.io.m21_import", "music21_import"),
    "pretty_midi": ("amads.io.pm_midi_import", "pretty_midi_import"),
    "mido": ("amads.io.mido_midi_import", "mido_midi_import"),
    "partitura": ("amads.io.pt_import", "partitura_import"),
}


def set_preferred_midi_reader(reader: str = _default_midi_reader) -> str:
    """
    Set a (new) preferred MIDI reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_midi_reader`.

    Parameters
    ----------
    reader : str, optional
        The name of the preferred MIDI reader; "music21", "pretty_midi",
        or "mido". Defaults to "mido".

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
    allowed = ["music21", "pretty_midi", "mido"]
    if reader not in allowed_subsystems["midi"]:
        raise ValueError(f"Invalid MIDI reader. Must be one of {allowed}")

    previous = preferred_midi_reader
    preferred_midi_reader = reader
    return previous


def set_preferred_xml_reader(reader: str = _default_xml_reader) -> str:
    """
    Set a (new) preferred XML reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_xml_reader`.

    Parameters
    ----------
    reader : str, optional
        The name of the preferred XML reader. Can be "music21" or "partitura".
        Defaults to "music21".

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
    allowed = allowed_subsystems["musicxml"]
    if reader not in allowed:
        raise ValueError(f"Invalid XML reader. Must be one of {allowed}")

    previous = preferred_xml_reader
    preferred_xml_reader = reader
    return previous


def set_preferred_kern_reader(reader: str = _default_kern_reader) -> str:
    """
    Set a (new) preferred Kern reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_kern_reader`.

    Parameters
    ----------
    reader : str, optional
        The name of the preferred Kern reader. Can be "music21" or "partitura".
        Defaults to "music21".

    Returns
    -------
    str
        The previous name of the preferred Kern reader.

    Raises
    ------
    ValueError
        If an invalid reader is provided.
    """
    global preferred_kern_reader
    allowed = allowed_subsystems["kern"]
    if reader not in allowed:
        raise ValueError(f"Invalid Kern reader. Must be one of {allowed}")

    previous = preferred_kern_reader
    preferred_kern_reader = reader
    return previous


def set_preferred_mei_reader(reader: str = _default_mei_reader) -> str:
    """
    Set a (new) preferred MEI reader.

    Returns the previous reader preference. The current preference is stored
    in `amads.io.reader.preferred_mei_reader`.

    Parameters
    ----------
    reader : str, optional
        The name of the preferred MEI reader. Can be "music21" or "partitura".
        Defaults to "music21".

    Returns
    -------
    str
        The previous name of the preferred MEI reader.

    Raises
    ------
    ValueError
        If an invalid reader is provided.
    """
    global preferred_mei_reader
    allowed = allowed_subsystems["mei"]
    if reader not in allowed:
        raise ValueError(f"Invalid MEI reader. Must be one of {allowed}")

    previous = preferred_mei_reader
    preferred_mei_reader = reader
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
    format: str,
) -> tuple[
    Optional[Callable[[str, str, bool, bool, bool, bool], Score]], Optional[str]
]:
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
    format : str
        The type of file to read: 'midi', 'musicxml', 'kern', or 'mei'.

    Returns
    -------
    tuple[Optional[Callable], Optional[str]]
        The import function if available, None otherwise.
    """
    preferred_reader = {
        "midi": preferred_midi_reader,
        "musicxml": preferred_xml_reader,
        "kern": preferred_kern_reader,
        "mei": preferred_mei_reader,
    }.get(format)

    if not preferred_reader:
        return None, preferred_reader

    try:
        if (
            preferred_reader not in _subsystem_map
            or preferred_reader not in allowed_subsystems[format]
        ):
            raise ValueError(
                f"Preferred reader '{preferred_reader}' not supported for "
                f"{format} import."
            )

        module_name, func_name = _subsystem_map[preferred_reader]
        module = __import__(module_name, fromlist=[func_name])
        return getattr(module, func_name), preferred_reader
    except Exception as e:
        print(f"Error importing {preferred_reader} for {format} files: {e}")
    return None, preferred_reader


def _import_score(
    filename: str | Path,
    format: str,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    group_by_instrument: bool = True,
) -> Score:
    """Import a score file

    <small>**Author**: Roger B. Dannenberg</small>
    """
    global _last_used_reader
    import_fn, preferred_reader = _check_for_subsystem(format)
    if import_fn is not None:
        _last_used_reader = import_fn
        if reader_warning_level != "none":
            print(
                f"Reading {str(filename)} using {format} reader "
                f"file={import_fn.__name__}."
            )
        return import_fn(
            str(filename), format, flatten, collapse, show, group_by_instrument
        )
    elif preferred_reader:
        raise Exception(
            f"Could not find an import function for file {str(filename)}, "
            f"format {format}. Preferred subsystem is {preferred_reader}"
        )
    else:
        raise Exception(
            "Could not identify a preferred subsystem or file format to "
            f"read file {str(filename)}, format {format}."
        )


def read_score(
    filename: str | Path,
    flatten: bool = False,
    collapse: bool = False,
    show: bool = False,
    format: Optional[str] = None,
    group_by_instrument: bool = True,
    ignore_hidden=False,
) -> Score:
    """Read a file with the given format, 'musicxml', 'midi', 'kern', 'mei'.

    If format is None (default), the format is based on the filename
    extension, which can be 'musicxml', 'mid', 'midi', 'smf', 'kern',
    or 'mei'. (Valid extensions are in
    `amads.io.readscore.valid_score_extensions`.)

    <small>**Author**: Roger B. Dannenberg</small>

    Parameters
    ----------
    filename : str | Path
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
        `'musicxml'`, `'midi'`, `'kern'`, `'mei'`)
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
    ignore_hidden: bool
        If False (default), MusicXML notes marked with `print-object="no"` are
        read and marked with the "hide_on_print" property set to True.
        If `ignore_hidden` is True, these notes are omitted from the AMADS score.

    Returns
    -------
    Score
        The imported score

    Raises
    ------
    ValueError
        If the format is unknown or not implemented.

    Note on Incomplete First Measure
    --------------------------------
    In Music21, the first measure may be a partial measure containing
    an anacrusis (“pickup”). This is somewhat ambiguous and does not
    translate well to MIDI which is less expressive than MusicXML.

    Therefore, if the first measure read with Music21 is not a full
    measure, a rest is inserted and the remainder is shifted to
    form a full measure according to its time signature. Remaining
    measures are shifted in time accordingly and Score, Part and
    Staff durations are adjusted accordingly.

    General MIDI Import Notes
    -------------------------
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

    Music21 has an optional 8vb treble clef. This becomes simply a
    treble clef (`Clef.clef == "treble") in AMADS.

    Some Music21 clefs are not supported in AMADS, e.g. tenor clef
    with an 8vb marking. These become `Clef.clef == "constructed"`
    and a tuple with (symbol, staff line, octave transposition) is
    stored as property "clef_info". Some unusual 18th, 19th, and 20th
    Century clefs are translated into more modern or conventional
    treble, soprano, alto, and tenor clefs, retaining the note
    positions on the staff, but not the original symbol.

    If a MusicXML note is marked with `print-object="no"`, the
    "hide_on_print" property will be set to True. You can access this
    with note.get("hide_on_print", False). Hidden notes as ornaments
    are independent of the standard ornaments described below.

    Grace notes are Notes marked by setting the `"is_grace"` property
    to True. AMADS also uses the `"has_slash"` property (no property
    means False) to indicate a grace note with a slash (conventionally
    an acciaccatura), but Music21 incorrectly sets its slash property
    by default, potentially losing slash information in MusicXML,
    where the default is no slash.

    Other Note properties are set as follows: `"has_trill"` and
    `"trill_pitch"` are set for Music21 Trill (`"trill_pitch"` has an
    AMADS Pitch object as its value); `"has_trill_extension"` is
    set for TrillExtension. `"has_turn"` and `"turn_pitches"` are set
    for Turn expressions (`"turn_pitches"` consists of a list with the
    upper pitch and the lower pitch as AMADS Pitch objects);
    `"has_inverted_turn"` and `"inverted_turn_pitches"` are set for
    InvertedTurn expressions (`"inverted_turn_pitches"` consists of a
    list with the lower pitch and the upper pitch as AMADS Pitch objects);
    `"has_mordent"` and `"mordent_pitch"` are set for Mordent
    expressions (`"mordent_pitch"` consists of the upper pitch as an
    AMADS Pitch object); `"has_inverted_mordent"` and
    `"inverted_mordent_pitch"` are set for InvertedMordent expressions
    (`"inverted_mordent_pitch"` consists of the upper pitch as an
    AMADS Pitch object); `"has_shake"` is set for Shake expressions;
    and `"has_schleifer"` is set for Schleifer expressions.
    """
    if isinstance(filename, str) and (
        filename.startswith("http") or "://" in filename
    ):
        with tempfile.NamedTemporaryFile(
            suffix=Path(filename).suffix or ".tmp", delete=False
        ) as tmp_file:
            urllib.request.urlretrieve(filename, tmp_file.name)
            filename = tmp_file.name

    if format is None:
        filename = Path(filename)
        ext = filename.suffix.lower()
        if ext not in [".pdf", ".ly"]:  # these are write-only extensions
            format = _suffix_to_format.get(ext)
        if not format:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Valid extensions: {valid_score_extensions}"
            )

    # File format handling
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter(
            "ignore" if reader_warning_level == "none" else "always"
        )

        score = _import_score(
            filename, format, flatten, collapse, show, group_by_instrument
        )

        # Warning handling
        if reader_warning_level == "low":
            if len(w) > 0:
                print(
                    f"Warning: {len(w)} warnings were generated in "
                    f"read_score({filename}).\n"
                    "  Use amads.io.readscore.set_reader_warning_level() "
                    "for more details."
                )
        else:  # "none", "default", or "high", but w is empty if "none"
            for warning in w:
                print(
                    f"{warning.filename}:{warning.lineno}: "
                    f"{warning.category.__name__}: {warning.message}"
                )

        return score


def last_used_reader() -> Optional[str]:
    """Return the name of the last used reader function.

    The reader function is an internal function called by `read_score`
    and based on the format, file name, and preferences in effect.

    Returns
    -------
    Optional[str]
        The name of the actual function used in the last call to `read_score`,
        or None if no reader has been used yet.
    """
    if _last_used_reader is not None:
        return _last_used_reader.__name__
    return None


# --------------- shared code for m21 and pt import -----------------


def _expand_first_measure(staff: Staff) -> float:
    """expand first measure to a full measure if necessary"""
    # what is the maximum offset of the first measure?
    shift = 0
    if len(staff.content) > 0:
        m1: Measure = cast(Measure, staff.content[0])
        m1_duration = m1.time_signature().duration
        max_offset = 0
        for elem in m1.content:
            max_offset = max(max_offset, elem.offset)
        if max_offset < m1_duration - 0.001:  # need to insert rest
            shift = m1_duration - max_offset
            for elem in m1.content:
                if (
                    isinstance(elem, Note)
                    or isinstance(elem, Rest)
                    or isinstance(elem, Chord)
                ):
                    elem.time_shift(shift)
            # insert Rest, Since m1 is first, m1.onset == 0
            _ = Rest(m1, m1.onset, duration=shift)
            m1.offset = m1_duration
            # now, first measure ending may have shifted, so adjust
            # remainder of the part
            if len(staff.content) > 1 and shift > 0.001:
                for m in staff.content[1:]:
                    # score.time_signatures has not been shifted yet, so
                    # look up the time signature for the meausure duration
                    # before shifting. We set the measure duration because
                    # partitura will give measure durations shorter than the
                    # time signature duration if the measure is not full
                    m.duration = m.time_signature().duration
                    m.time_shift(shift)
            staff.offset = staff.content[-1].offset
            # update Part offset:
            part = staff.parent
            part.offset = max(part.offset, staff.offset)
            # update Score offset:
            score = part.parent
            score.offset = max(score.duration, staff.offset)
    return shift


def _finish_import(
    score: Score, flatten: bool, collapse: bool, shift: float
) -> Score:
    """Apply some final manipulations common to m21 and pt import"""
    if shift > 0.001:
        # parts are shifted but not measures and time signatures.
        # shared_shift is in beats
        score.time_map._time_shift(shift)
        score._timesignatures_shift(shift)
    if flatten or collapse:
        score = score.flatten(collapse=collapse)
    return score
