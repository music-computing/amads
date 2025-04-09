"""
Implementation of the contour classification scheme proposed by Huron (1996) [1]
and also included in the FANTASTIC toolbox of Müllensiefen (2009) [2]
(Features 19 `Huron Contour: h.contour`).
"""

__author__ = "Mark Gotham"

from utils import sign


class HuronContour:
    """Implementation of the contour classification scheme proposed by Huron (1996) [1]
    and also included in the FANTASTIC toolbox of Müllensiefen (2009) [2]
    (Features 19 `Huron Contour: h.contour`).

    Huron categorises melodies by identifying the start, mean, and end pitches
    and describing contour in terms of the two directions: start-mean, and mean-end.
    """

    def __init__(self, pitches: list[int], times: list[float], method: str = "amads"):
        """Initialize with pitch and time values.

        Parameters
        ----------
        pitches : list[int]
            Pitch values in any numeric format (e.g., MIDI numbers).
        times : list[float]
            Onset times in any consistent, proportional scheme (e.g., seconds, quarter notes, etc.)

        Raises
        ------
        ValueError
            If the `times` and `pitches` parameters are not the same length.

        Examples
        --------
        >>> happy_birthday_pitches = [
        ...     60, 60, 62, 60, 65, 64, 60, 60, 62, 60, 67, 65,
        ...     60, 60, 72, 69, 65, 64, 62, 70, 69, 65, 67, 65
        ... ]
        >>> happy_birthday_times = [
        ...     0, 0.75, 1, 2, 3, 4, 6, 6.75, 7, 8, 9, 10,
        ...     12, 12.75, 13, 14, 15, 16, 17, 18, 18.75, 19, 20, 21
        ... ]
        >>> hc = HuronContour(
        ...     happy_birthday_pitches,
        ...     happy_birthday_times,
        ... )

        >>> hc.first_pitch
        60
        >>> hc.mean_pitch
        65
        >>> hc.last_pitch
        65
        >>> hc.first_to_mean
        5
        >>> hc.mean_to_last
        0
        >>> hc.contour_class
        'Ascending-Horizontal'

        References
        ----------
        [1] Huron, D (2006). The Melodic Arch in Western Folksongs. Computing in Musicology 10.
        [2] Müllensiefen, D. (2009). Fantastic: Feature ANalysis Technology Accessing
        STatistics (In a Corpus): Technical Report v1.5
        """
        if len(times) != len(pitches):
            raise ValueError(
                f"Times and pitches must have the same length, got {len(times)} and {len(pitches)}"
            )

        self.times = times
        self.pitches = pitches
        self.first_pitch = pitches[0]
        self.last_pitch = pitches[-1]

        self.mean_pitch = None
        self.first_to_mean = None
        self.mean_to_last = None
        self.calculate_mean_attributes()

        self.contour_class = None
        self.class_label()

    def calculate_mean_attributes(self):
        """
        Calculate the mean and populate the remaining attributes.
        Note that the mean pitch is rounded to the nearest integer,
        and that this rounding happens before calculating comparisons.
        """
        self.mean_pitch = int(
            sum(x * y for x, y in zip(self.pitches, self.times)) / sum(self.times)
        )

        self.first_to_mean = self.mean_pitch - self.first_pitch
        self.mean_to_last = self.last_pitch - self.mean_pitch

    def class_label(self):
        """Classify a contour into Huron's categories.
        This is based simply on the two directions from start to mean and mean to last.
        Huron proposes shorthands for some of these as follows:
        "Ascending-Descending" = "Convex",
        "Ascending-Horizontal" = None,
        "Ascending-Ascending": None,
        "Horizontal-Descending": None,
        "Horizontal-Horizontal": "Horizontal",
        "Horizontal-Ascending": None,
        "Descending-Descending": "Descending",
        "Descending-Ascending": "Concave"

        Where no shorthand is provided, this method return the longhand.

        Returns
        -------
        str
            String, exactly as reported in the FANTASTIC library.

        """

        direction_dict = {-1: "Descending", 0: "Horizontal", 1: "Ascending"}

        first_to_mean_sign = sign(self.first_to_mean)
        mean_to_last_sign = sign(self.mean_to_last)

        return_string = (
            f"{direction_dict[first_to_mean_sign]}-{direction_dict[mean_to_last_sign]}"
        )

        shorthand_dict = {
            "Ascending-Descending": "Convex",
            "Horizontal-Horizontal": "Horizontal",
            "Descending-Descending": "Descending",
            "Descending-Ascending": "Concave",
        }

        if return_string in shorthand_dict:
            self.contour_class = shorthand_dict[return_string]
        else:
            self.contour_class = return_string
