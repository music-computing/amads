"""
Convert a frequency in Hertz to the corresponding (float) MIDI pitch number. (From MIDI Toolbox)

Original doc: MIDI Tooolbox (https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=63)
"""

import math


def hz2midi(hertz):
    """
    Convert a frequency in Hertz to the corresponding MIDI note number.

    Validates input to ensure all frequencies are non-negative.

    Parameters
    ----------
    hertz : Union[float, list[float]]
        The frequency or list of frequencies in Hertz.

    Returns
    -------
    Union[float, list[float]]
        The corresponding MIDI note number or list of numbers (A4 = 440Hz = 69).

    Raises
    ------
    ValueError
        If any frequency is negative.

    Examples
    --------
    >>> hz2midi(440.0)
    69.0
    >>> hz2midi([440.0, 880.0])
    [69.0, 81.0]
    """

    def validate_hz(hz):
        if hz < 0:
            raise ValueError(f"The frequency of a sound must be non-negative, got {hz}")

    if isinstance(hertz, list):
        for hz in hertz:
            validate_hz(hz)
        return [69 + 12 * math.log2(hz / 440.0) for hz in hertz]
    else:
        validate_hz(hertz)
        return 69 + 12 * math.log2(hertz / 440.0)
