"""
Musical instruments have different attributes and require different actions.
This module currently focuses on cases where specific pitches map (almost) unambiguously to a corresponding fingering.

This module serves to model basic elements of instrument structure and fingering.
To be clear, this is about modelling those aspects of playing an instrument concerned with
engaging specific instrument keys/valves/holes using a given finger (or thumb).
This is quite far removed from the notational practice of showing a finger number on a stave.
As elsewhere in this toolkit, we are concerned with the underlying structures rather than the notational manifestation.

In the case of "wind" (woodwind and brass) instruments, there is an almost 1:1 mapping of finger use with valve or key.
For example, playing the modern valve trumpet involved a 1:1 mapping of 3 fingers to 3 corresponding valves
(and a 4th operating a slider in a subsidiary role).
Similarly, the modern, Boehm flute uses all 8 fingers and
one thumb (the RH thumb is only for support),
though there are more elements here:
some fingers operate multiple keys
(the RH 5th finger operates 3 keys, and the LH little finger has two: B and "Briccialdi" for Bb)
and some keys are never (or rarely) used.

This preferred finger/valve combination for a given pitch is clearest in lower octaves.
Higher up the situation is more complex:
the number of possible fingerings increases and the relative preference between those options decreases.
In the future, we may consider encoding "alternatives" and even "confidence values" to model this.

Overall, given this situation, we organise this code around the instrument (keys/valves/holes, which are unambiguous),
while keeping a default but flexible mapping to the fingers used for use in applications like
learning about musical difficulty focused on the ergonomic challenges of specific fingering transitions.
"""

__author__ = "Mark Gotham"


from typing import Union


class Finger:
    """Encode a model of fingers and thumbs."""

    def __init__(self, hand: str, name: str, number: int):
        self.hand = hand.lower()
        self.name = name.lower()
        self.number = number
        self.run_checks()

    def run_checks(self):
        if self.hand not in ["left", "right"]:
            raise ValueError
        if self.name not in ["thumb", "index", "middle", "ring", "little"]:
            raise ValueError
        if self.number not in range(5):
            raise ValueError


FINGERS = [
    Finger("left", "thumb", 0),
    Finger("left", "index", 1),
    Finger("left", "middle", 2),
    Finger("left", "ring", 3),
    Finger("left", "little", 4),
    Finger("right", "thumb", 0),
    Finger("right", "index", 1),
    Finger("right", "middle", 2),
    Finger("right", "ring", 3),
    Finger("right", "little", 4),
]


class WindInstrument:
    """
    Base class for "wind" instruments (including "brass" and "woodwind")
    with the expectation (but not requirement) of having valves, keys, holes, or equivalent.
    These are "non-free aerophones" in the Hornbostel–Sachs classification.

    Objects of this class encode list of
    the key (e.g., flute), valve (e.g., trumpet), or hole (e.g., record) in a shared representation, equivalently.
    They also encode default mappings showing the usual fingering combination used to achieve a specific pitch.
    """

    def __init__(self, name):
        self.name = name
        self.keys_valves_holes = []
        self.pitch_key_combination_map = {}


class KeyValveHole:
    """
    Shared object for an instrument's key (e.g., flute), valve (e.g., trumpet), or hole (e.g., record).
    The name is a free string, for flexibility wrt the different instruments.
    The `finger` is a default used to engage this key/valve/hole or else
    a list thereof (in order or preference).
    """

    def __init__(self, name: str, finger: Union[Finger, list[Finger]]):
        self.name = name
        self.finger = finger


class Trumpet(WindInstrument):
    """
    The modern valve trumpet.

    No valves for C4:

    >>> trumpet =  Trumpet()
    >>> pitch = "C4"
    >>> valves = [x.name for x in trumpet.pitch_key_combination_map[pitch]]
    >>> valves
    []

    One for B3:

    >>> pitch = "B3"
    >>> valves = [x.name for x in trumpet.pitch_key_combination_map[pitch]]
    >>> valves
    ['Valve 2']
    """

    def __init__(self):
        super().__init__("Trumpet")
        self.keys_valves_holes = [
            KeyValveHole("Valve 1", [FINGERS[1]]),
            KeyValveHole("Valve 2", [FINGERS[2]]),
            KeyValveHole("Valve 3", [FINGERS[3]]),
        ]

        self.pitch_key_combination_map = {
            "F#3": [0, 1, 2],
            "G3": [0, 2],
            "G#3": [1, 2],
            "A3": [0, 1],
            "Bb3": [0],
            "B3": [1],
            "C4": [],
            # ... TODO continue for all trumpet pitch:fingering mappings
        }
        for k, v in self.pitch_key_combination_map.items():
            self.pitch_key_combination_map[k] = [self.keys_valves_holes[x] for x in v]


class Flute(WindInstrument):
    """
    The Boehm flute.

    >>> flute =  Flute()
    >>> finger_name_hand = [x.name for x in flute.pitch_key_combination_map["A4"]]
    >>> finger_name_hand
    ['B Key', 'C Key', 'A Key', 'D# Key']
    """

    def __init__(self):
        super().__init__("Flute")
        self.keys_valves_holes = [
            # Left:
            KeyValveHole("B Key", [FINGERS[0]]),  # thumb
            KeyValveHole("Bb Key", [FINGERS[0]]),  # also left thumb, sic
            KeyValveHole("C Key", [FINGERS[1]]),  # index
            KeyValveHole("A Key", [FINGERS[2]]),  # middle
            KeyValveHole("G Key", [FINGERS[3]]),  # ring
            KeyValveHole("G# Key", [FINGERS[4]]),  # little
            # Right
            KeyValveHole("F Key", [FINGERS[6]]),  # index
            KeyValveHole("E Key", [FINGERS[2]]),  # middle
            KeyValveHole("D Key", [FINGERS[3]]),  # ring
            KeyValveHole("D# Key", [FINGERS[9]]),  # little (default)
            KeyValveHole("C# Key", [FINGERS[9]]),  # also little, sic
            KeyValveHole("Low C Key", [FINGERS[9]]),  # "
            KeyValveHole("Low B Key", [FINGERS[9]]),  # "
            # TODO trill keys etc.
        ]
        self.pitch_key_combination_map = {  # TODO retrieve by name?
            "A4": [
                self.keys_valves_holes[0],
                self.keys_valves_holes[2],
                self.keys_valves_holes[3],
                self.keys_valves_holes[9],
            ],
            # ... TODO continue for all flute pitch:fingering mappings
        }


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import doctest

    doctest.testmod()
