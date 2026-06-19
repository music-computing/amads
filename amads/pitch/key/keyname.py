"""
Convert MIDI Toolbox key codes to key names (text).

Key codes are the integers returned by some MIDI Toolbox key-finding functions
(1--12 major, 13--24 minor), not ``kkkey`` indices (0--11 with a separate mode).
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

    Parameters
    ----------
    attribute : str
        ``"major"`` or ``"minor"`` (as returned by :func:`~amads.pitch.key.kkkey.kkkey`).
    key_index : int
        Tonic index 0--11 where 0 is C (as returned by ``kkkey``).

    Returns
    -------
    int
        Key code in 1--24 for use with :func:`keyname`.

    Raises
    ------
    ValueError
        If ``attribute`` is not ``"major"`` or ``"minor"``, or ``key_index`` is
        not in ``0..11``.
    """
    if key_index < 0 or key_index > 11:
        raise ValueError(f"key_index must be 0..11, got {key_index}")
    if attribute == "major":
        return key_index + 1
    if attribute == "minor":
        return key_index + 13
    raise ValueError(f"attribute must be 'major' or 'minor', got {attribute!r}")


def keyname(
    n: Union[int, Iterable[int]], detail: bool = True
) -> Union[str, List[str]]:
    """Convert MIDI Toolbox key codes to key-name strings.

    Key encoding: 1--12 = C major … B major; 13--24 = c minor … b minor.

    <small>**Author**: Tai Nakamura</small>

    Parameters
    ----------
    n : int or iterable of int
        Key code(s) (e.g. from MIDI Toolbox key-finding functions).
    detail : bool, optional
        If ``True`` (default), return short spellings (``C#``). If ``False``,
        return enharmonic pairs (``C#/Db``). Note: the MIDI Toolbox header
        comment for ``keyname`` disagrees with its implementation; AMADS
        follows the implementation.

    Returns
    -------
    str or list of str
        Key name(s) for each code in ``n``.

    Raises
    ------
    ValueError
        If any code is not in ``1..24``.

    See Also
    --------
    keycode_from_kkkey : Convert :func:`~amads.pitch.key.kkkey.kkkey` output to
        key codes.
    amads.core.utils.key_num_to_name : MIDI key numbers (e.g. 60 = C4).

    References
    ----------
    - Toiviainen, P., & Eerola, T. (2016). MIDI Toolbox 1.1. URL:
      https://github.com/miditoolbox/1.1

    Examples
    --------
    >>> keyname(1)
    'C'
    >>> keyname(13)
    'c'
    >>> keyname([1, 14], detail=False)
    ['C', 'c#/db']
    """
    if isinstance(n, int):
        return _keyname_one(n, detail)
    return [_keyname_one(code, detail) for code in n]


def _keyname_one(n: int, detail: bool) -> str:
    if n < 1 or n > 24:
        raise ValueError(f"key code must be 1..24, got {n}")
    if detail:
        major, minor = _KEYNAME_MAJOR_SHORT, _KEYNAME_MINOR_SHORT
    else:
        major, minor = _KEYNAME_MAJOR_LONG, _KEYNAME_MINOR_LONG
    if n < 13:
        return major[n - 1]
    return minor[n - 13]
