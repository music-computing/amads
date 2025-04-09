# -*- coding: utf-8 -*-
"""
Parsons code for contour of musical melody by direction only.
"""

from typing import Optional

from utils import sign

__author__ = "Mark Gotham"


class ParsonsContour:
    """Implementation of the basic Parsons contour classification scheme.

    Parsons categorises each step by direction only.

    Nothing more, nothing less.
    """

    def __init__(
        self,
        pitches: list[int],
        character_dict: Optional[dict] = None,
        initial_asterisk: bool = False,
    ):
        """
        The 'Parsons code' returns simply the direction of each successive melodic interval.
        It's been used in lookup, and can serve as a useful first entry point to the topic of contour.

        Parameters
        ----------
        pitches:
            A list of integers representing pitches
            (assumed to be MIDI numbers or equivalent, not pitch classes)
        character_dict:
            A dict specifying which characters to use when mapped to a string.
            Must include keys for [1, 0, -1] corresponding to up, repeat, and down.
            The default is Parsons' own values: {1: "u", 0: "r", -1: "d"}.
            Other options could include `<`, `=`, `>`.
        initial_asterisk:
            Optionally, include an initial `*` for the start of the sequence (no previous interval).

        Examples
        --------
        >>> happy = [60, 60, 62, 60, 65, 64, 60, 60, 62, 60, 67, 65, 60, 60, 72, 69, 65, 64, 62, 70, 69, 65, 67, 65]
        >>> pc = ParsonsContour(happy)
        >>> pc.interval_sequence
        [None, 0, 2, -2, 5, -1, -4, 0, 2, -2, 7, -2, -5, 0, 12, -3, -4, -1, -2, 8, -1, -4, 2, -2]

        >>> pc.interval_sequence_sign
        [None, 0, 1, -1, 1, -1, -1, 0, 1, -1, 1, -1, -1, 0, 1, -1, -1, -1, -1, 1, -1, -1, 1, -1]

        >>> pc.as_string
        'rududdrududdrudddduddud'

        >>> twinkle_ints = [72, 72, 79, 79, 81, 81, 79, 77, 77, 76, 76, 74, 74, 72]
        >>> pc = ParsonsContour(twinkle_ints)
        >>> pc.as_string
        'rururddrdrdrd'

        >>> pc_no_asterisk = ParsonsContour(twinkle_ints, initial_asterisk=True)
        >>> pc_no_asterisk.as_string
        '*rururddrdrdrd'

        >>> pc_symbols = ParsonsContour(twinkle_ints, {1: "<", 0: "=", -1: ">"})
        >>> pc_symbols.as_string
        '=<=<=>>=>=>=>'

        References
        ----------
        [1] Parsons, Denys. 1975. The Directory of Tunes and Musical Themes.
        """

        self.pitches = pitches
        self.character_dict = (
            character_dict if character_dict else {1: "u", 0: "r", -1: "d"}
        )
        self.initial_asterisk = initial_asterisk

        self.interval_sequence = None
        self.interval_sequence_sign = None
        self.as_string = None

        self.get_intervals()
        self.make_string()

    def get_intervals(self):
        self.interval_sequence = [
            None
        ]  # Now as lists, still initialised with None, as per AMADS policy ...
        self.interval_sequence_sign = [None]
        for i in range(len(self.pitches) - 1):
            this_diff = self.pitches[i + 1] - self.pitches[i]
            self.interval_sequence.append(this_diff)
            self.interval_sequence_sign.append(sign(this_diff))

    def make_string(self):
        """Create a flat, string representation of the contour directions."""
        self.as_string = ""
        if self.initial_asterisk:
            self.as_string += "*"
        for i in range(1, len(self.interval_sequence_sign)):
            self.as_string += self.character_dict[self.interval_sequence_sign[i]]


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
