"""
MIDI Toolbox key-name conversion.

Also provides ``keycode_from_kkkey`` to map [kkkey][amads.pitch.key.kkkey.kkkey]
output to MIDI Toolbox key codes (1--24).

<small>**Author**: Tai Nakamura</small>

Reference
---------
https://github.com/miditoolbox/1.1/blob/master/documentation/MIDItoolbox1.1_manual.pdf, page 67.
"""

from typing import Iterable, List, Union

_KEYNAME_MAJOR_SHORT = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)
_KEYNAME_MINOR_SHORT = tuple(s.lower() for s in _KEYNAME_MAJOR_SHORT)

_KEYNAME_MAJOR_LONG = (
    "C",
    "C#/Db",
    "D",
    "D#/Eb",
    "E",
    "F",
    "F#/Gb",
    "G",
    "G#/Ab",
    "A",
    "A#/Bb",
    "B",
)
_KEYNAME_MINOR_LONG = tuple(s.lower() for s in _KEYNAME_MAJOR_LONG)


def keycode_from_kkkey(attribute: str, key_index: int) -> int:
    """Map a ``kkkey`` result to a MIDI Toolbox key code (1--24).

    AMADS-only helper: MIDI Toolbox ``kkkey`` already returns codes 1--24,
    while [kkkey][amads.pitch.key.kkkey.kkkey] returns ``(attribute, key_index)``
    with ``key_index`` in ``0..11``.

    Parameters
    ----------
    attribute : str
        ``"major"`` or ``"minor"`` (as returned by ``kkkey``).
    key_index : int
        Tonic index 0--11 where 0 is C (as returned by ``kkkey``).

    Returns
    -------
    int
        Key code in 1--24 for use with [keyname][amads.pitch.key.keyname.keyname].

    Raises
    ------
    ValueError
        If ``attribute`` is not ``"major"`` or ``"minor"``, or ``key_index`` is
        not in ``0..11``.

    See Also
    --------
    [kkkey][amads.pitch.key.kkkey.kkkey] : Estimate the key of a score.
    [keyname][amads.pitch.key.keyname.keyname] : Convert key codes to key-name strings.

    Examples
    --------
    >>> from amads.core.basics import Score
    >>> from amads.pitch.key.kkkey import kkkey
    >>> score = Score.from_melody([67, 69, 71, 72, 74, 76, 78, 79]) # G major
    >>> attribute, key_index = kkkey(score)
    >>> keycode_from_kkkey(attribute, key_index)
    8
    >>> keyname(keycode_from_kkkey(attribute, key_index))
    'G'
    """
    if key_index < 0 or key_index > 11:
        raise ValueError(f"key_index must be 0..11, got {key_index}")
    if attribute == "major":
        return key_index + 1
    if attribute == "minor":
        return key_index + 13
    raise ValueError(f"attribute must be 'major' or 'minor', got {attribute!r}")


def keyname(
    n: Union[int, Iterable[int]], detail: bool = False
) -> Union[str, List[str]]:
    """Implementation of the ``keyname`` function in the Matlab MIDI Toolbox.

    Key codes are integers 1--24 (major 1--12, minor 13--24), as returned by
    MIDI Toolbox key-finding functions such as ``kkkey``. They are not the same
    as ``kkkey`` indices (``0..11`` plus a separate mode attribute).

    Major keys use uppercase spellings (``C``, ``C#``, …, ``B``); minor keys use
    lowercase spellings (``c``, ``c#``, …, ``b``), matching the MIDI Toolbox
    convention.

    Parameters
    ----------
    n : int or iterable of int
        Key code(s) to convert.
    detail : bool, optional
        If ``False`` (default), return short spellings (``C#`` / ``c#``). If
        ``True``, return enharmonic pairs (``C#/Db`` / ``c#/db``).

    Returns
    -------
    str or list of str
        Key name(s). A single code returns a string; an iterable returns a list.

    Raises
    ------
    ValueError
        If any code is not in ``1..24``.

    See Also
    --------
    [kkkey][amads.pitch.key.kkkey.kkkey] : Estimate the key of a score.
    [keycode_from_kkkey][amads.pitch.key.keyname.keycode_from_kkkey] : Convert AMADS ``kkkey`` output to key codes 1--24.
    key_num_to_name : Convert MIDI key numbers (e.g. 60 = C4) to note names.

    Examples
    --------
    >>> from amads.core.basics import Score
    >>> from amads.pitch.key.kkkey import kkkey
    >>> score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    >>> attribute, key_index = kkkey(score)
    >>> keyname(keycode_from_kkkey(attribute, key_index))
    'C'
    >>> keyname(1)
    'C'
    >>> keyname(13)
    'c'
    >>> keyname(2, detail=True)
    'C#/Db'
    >>> keyname([1, 14], detail=True)
    ['C', 'c#/db']
    """
    if detail:
        major, minor = _KEYNAME_MAJOR_LONG, _KEYNAME_MINOR_LONG
    else:
        major, minor = _KEYNAME_MAJOR_SHORT, _KEYNAME_MINOR_SHORT

    if isinstance(n, int):
        codes: Iterable[int] = (n,)
        single = True
    else:
        codes = n
        single = False

    names: List[str] = []
    for code in codes:
        if code < 1 or code > 24:
            raise ValueError(f"key code must be 1..24, got {code}")
        if code < 13:
            names.append(major[code - 1])
        else:
            names.append(minor[code - 13])
    return names[0] if single else names
