import math

from ..io.ptscoreread import score_read, score_read_extensions
from .basics import Pitch


def dir2coll(filenames):
    """
    Converts a list of music filenames to a dictionary where keys
    are filenames and values are corresponding Score objects.

    Parameters:
    filenames (list of str): List of filenames to process.

    Returns:
    scores (dict): A dictionary mapping filenames to Score objects.
    """
    scores = {}
    valid_extensions = score_read_extensions()

    for file in filenames:
        if any(file.endswith(ext) for ext in valid_extensions):
            try:
                score = score_read(file)
                scores[file] = score
            except Exception as e:
                print(f"Error processing file {file}: {e}")
        else:
            print(f"Unsupported file format: {file}")

    return scores


def hz2num(hertz):
    """
    Converts a frequency in Hertz to the corresponding MIDI key number.

    Parameters:
    hertz (float or list of floats): The frequency or list of frequencies
    in Hertz.

    Returns:
    num (Pitch or list of Pitch): The corresponding MIDI key number(s)
    as Pitch objects.
    """

    def hz_to_num_single(hz):
        num = 69 + 12 * math.log2(hz / 440.0)
        return Pitch(round(num))

    if isinstance(hertz, list):
        return [hz_to_num_single(hz) for hz in hertz]
    else:
        return hz_to_num_single(hertz)


def num2hz(num):
    """
    Converts a Pitch object or MIDI key number to the corresponding
    frequency in Hertz.

    Parameters:
    num (Pitch or int or list of Pitch or ints): The Pitch object(s) or
    MIDI key number(s).

    Returns:
    hz (float or list of floats): The corresponding frequency in Hertz.
    """

    def num_to_hz_single(k):
        if isinstance(k, Pitch):
            num = k.num
        else:
            num = k
        return 440.0 * 2 ** ((num - 69) / 12)

    if isinstance(num, list):
        return [num_to_hz_single(k) for k in num]
    else:
        return num_to_hz_single(num)


def keyname(n, detail="nameoctave"):
    """
    Converts key numbers to key names (text).

    Parameters:
    n (int or list of ints): The key numbers.
    detail (str, optional): 'nameonly' for just the note name (e.g., 'C#'),
                            'nameoctave' for note name with octave
                            (e.g., 'C#4') (default).

    Returns:
    name (str or list of str): The corresponding key names.
    """

    def keyname_single(k):
        pitch = Pitch(k)
        if detail == "nameonly":
            return pitch.name  # Handles sharps, flats, and natural notes correctly
        elif detail == "nameoctave":
            return pitch.name_with_octave  # Includes both the note name and octave
        else:
            raise ValueError(
                "Invalid detail option. Use 'nameonly' or " "'nameoctave'."
            )

    if isinstance(n, list):
        return [keyname_single(k) for k in n]
    else:
        return keyname_single(n)
