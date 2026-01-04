import math
from typing import Iterator, Optional, Union

from amads.core.basics import Pitch
from amads.io.readscore import read_score, valid_score_extensions


def dir_to_collection(filenames: list[str]):
    """
    Converts a list of music filenames to a dictionary where keys
    are filenames and values are corresponding Score objects.

    Parameters
    ----------
    filenames : list(str)
        List of filenames to process.

    Returns
    -------
    dict
        A dictionary mapping filenames to Score objects.
    """
    scores = {}

    for file in filenames:
        if any(file.endswith(ext) for ext in valid_score_extensions):
            try:
                score = read_score(file)
                scores[file] = score
            except Exception as e:
                print(f"Error processing file {file}: {e}")
        else:
            print(f"Unsupported file format: {file}")

    return scores


def _hz_to_key_num_single(hz: float, do_round: bool = True) -> float:
    """Helper function for hz_to_key_num"""
    key_num = 69 + 12 * math.log2(hz / 440.0)
    return round(key_num) if do_round else key_num


def hz_to_key_num(
    hertz: Union[float, list[float]], do_round: bool = True
) -> Union[float, list[float]]:
    """
    Converts a frequency in Hertz to the corresponding MIDI key number.

    Parameters
    ----------
    hertz : Union(float, list(float))
        The frequency or list of frequencies in Hertz.

    do_round : bool
        Perform rounding to the nearest integer key_num.

    Returns
    -------
    Union(float, list(float))
        The corresponding MIDI key number(s).

    Examples
    --------
    >>> hz_to_key_num(440.0)
    69
    >>> hz_to_key_num(260.0, False)
    59.89209719404554
    >>> hz_to_key_num([440, 260], True)
    [69, 60]
    """

    if isinstance(hertz, list):
        return [_hz_to_key_num_single(hz, do_round) for hz in hertz]
    else:
        return _hz_to_key_num_single(hertz, do_round)


def hz_to_pitch(
    hertz: Union[float, list[float]], round: bool = True
) -> Union[Pitch, list[Pitch]]:
    """
    Converts a frequency to a Pitch object.

    Parameters
    ----------
    hertz : Union(float, list(float))
        The frequency or list of frequencies in Hertz.

    round : bool
        Perform rounding to the nearest integer key_num.

    Returns
    -------
    Union(Pitch, list(Pitch))
        The corresponding Pitch objects.

    Examples
    --------
    >>> hz_to_pitch(440)
    Pitch(name='A4', key_num=69)
    """
    key_nums = hz_to_key_num(hertz, round)
    if isinstance(key_nums, list):
        return [Pitch(kn) for kn in key_nums]
    else:
        return Pitch(key_nums)


def key_num_to_hz(
    key_num: Union[float, Pitch, list[Union[float, Pitch]]]
) -> Union[float, list[float]]:
    """
    Converts a Pitch object or MIDI key number to the corresponding
    frequency in Hertz.

    Parameters
    ----------
    key_num : Union(Pitch, float, list(Union(Pitch, float)))
        The Pitch object(s) or MIDI key number(s).

    Returns
    -------
    Union(float, list(float))
        The corresponding frequency in Hertz.

    Examples
    --------
    >>> key_num_to_hz(69)
    440.0
    >>> key_num_to_hz([Pitch("A5"), 60])
    [880.0, 261.6255653005986]
    """

    def key_num_to_hz_single(k):
        if isinstance(k, Pitch):
            key_num = k.key_num
        else:
            key_num = k
        return 440.0 * 2 ** ((key_num - 69) / 12)

    if isinstance(key_num, list):
        return [key_num_to_hz_single(k) for k in key_num]
    else:
        return key_num_to_hz_single(key_num)


def key_num_to_name(n, detail="nameoctave"):
    """
    Converts key numbers to key names (text).

    Parameters
    ----------
    n : Union(int, list(int))
        The key numbers.
    detail : Optional(str)
        `'nameonly'` for just the note name (e.g., `'C#'`),
        `'nameoctave'` for note name with octave (e.g., `'C#4'`) (default).

    Returns
    -------
    Union(str, list(str))
        The corresponding key names.
    """

    def key_num_to_name_single(k):
        pitch = Pitch(k)
        if detail == "nameonly":
            # Handles sharps, flats, and naturals correctly
            return pitch.name
        elif detail == "nameoctave":
            return pitch.name_with_octave  # Includes note name and octave
        else:
            raise ValueError(
                "Invalid detail option. Use 'nameonly' or " "'nameoctave'."
            )

    if isinstance(n, list):
        return [key_num_to_name_single(k) for k in n]
    else:
        return key_num_to_name_single(n)


def sign(x: float) -> int:
    """
    Get the sign of a numeric value as -1, 0, or +1.

    Returns
    ----------
    int
        -1 if `x` < 0, 0 if `x` == 0, 1 if `x` > 0

    Examples
    --------
    >>> sign(-15)
    -1

    >>> sign(-1)
    -1

    >>> sign(-0.5)
    -1

    >>> sign(-0)
    0

    >>> sign(+0)
    0

    >>> sign(+0.5)
    1

    >>> sign(15.2)
    1

    >>> sign(None) is None
    True
    """
    if x is None:
        return None  # type: ignore
    else:
        return bool(x > 0) - bool(x < 0)


def float_range(
    start: float, end: Optional[float], step: float
) -> Iterator[float]:
    """Generate a range of floats.

    Similar to Python's built-in range() function but supports floating
    point numbers. If end is None, generates an infinite sequence.

    Parameters
    ----------
    start : float
        The starting value of the range
    end : float or None
        The end value of the range (exclusive). If None, generates an
        infinite sequence
    step : float
        The increment between values

    Yields
    ------
    float
        The next value in the sequence
    """
    curr = start
    while end is None or curr < end:
        yield curr
        curr += step


def check_python_package_installed(package_name: str):
    """
    Check if a Python package is installed, raise error if not.

    Parameters
    ----------
    package_name : str
        Name of the package to check

    Raises
    ------
    ImportError
        If package is not installed, with message suggesting pip install
    """
    try:
        __import__(package_name)
    except ImportError:
        raise ImportError(
            f"Package '{package_name}' is required but not installed. "
            f"Please install it using: pip install {package_name}"
        )
