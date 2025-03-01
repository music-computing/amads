"""Ports `pianoroll` Function

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=82
"""

import matplotlib.pyplot as plt
from matplotlib import figure, patches

from ..core.basics import Part, Score


def midi_num_to_name(midi_num: int, accidental) -> str:
    """Converts midi numbers to note names

    Helper function for pianoroll

    Args:
        midi_num (int):
            The midi number to be converted
        accidental (str):
            If the note has an accidental, determines if
            it is a sharp or a flat. Valid input: 'sharp' or 'flat'.

    Returns:
        A string representing the name of the note that matches the
        input MIDI number.

    Raises:
        ValueError: If there are invalid input argument.
    """

    octave = str(int((midi_num / 12) - 1))

    match accidental:
        case "sharp":
            base = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][
                midi_num % 12
            ]
        case "flat":
            base = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"][
                midi_num % 12
            ]

    return base + octave


def pianoroll(
    score: Score, y_label="name", x_label="beat", color="skyblue", accidental="sharp"
) -> figure.Figure:
    """Converts a Score to a piano roll display of a musical score.

    Args:
        score (Score):
            The musical score to display
        y_label (str, optional):
            Determines whether the y-axis is
            labeled with note names or MIDI numbers.
            Valid Input: 'name' or 'num'.
        x_label (str, optional):
            Determines whether the x-axis is labeled
            with beats or seconds. Valid input: 'beat' or 'sec'.
        accidental (str, optional):
            Determines whether the y-axis is
            labeled with sharps or flats. O nly useful if argument
            y_label is 'name'. Raises exception on inputs that's not
            'sharp' or 'flat'.

    Returns:
        A matplotlib.figure.Figure of a pianoroll diagram.

    Raises:
        ValueError: If there are invalid input argument.
    """

    # Check for correct x_label input argument
    if x_label != "beat" and x_label != "sec":
        raise ValueError("Invalid x_label type")

    fig, ax = plt.subplots()

    min_note, max_note = 127.0, 0.0
    max_time = 1  # plot at least 1 second or beat
    # remove ties and make a sorted list of all notes:
    score = score.flatten(collapse=True)
    for note in next(score.find_all(Part)).content:
        onset_time = note.onset
        offset_time = note.offset
        pitch = note.keynum - 0.5

        # Conditionally converts beat to sec
        if x_label == "sec":
            onset_time = score.time_map.beat_to_time(onset_time)
            offset_time = score.time_map.beat_to_time(offset_time)

        # Stores min and max note for y_axis labeling
        if pitch < min_note:
            min_note = pitch
        if pitch > max_note:
            max_note = pitch

        # Stores max note start time + note duration for x_axis limit
        if offset_time > max_time:
            max_time = offset_time

        # Draws the note
        print("draw note from", onset_time, "to", offset_time, "at", pitch)
        rect = patches.Rectangle(
            (onset_time, pitch),
            offset_time - onset_time,
            1,
            edgecolor="black",
            facecolor=color,
        )
        ax.add_patch(rect)

    # Determines correct axis labels
    if min_note == 127 and max_note == 0:  # "fake" better axes:
        min_note = 59
        max_note = 59

    midi_numbers = list(range(int(min_note), int(max_note + 2)))

    match y_label:
        case "num":
            notes = midi_numbers
        case "name":
            notes = [midi_num_to_name(mn, accidental) for mn in midi_numbers]
        case _:
            raise ValueError("Invalid y_label type")

    # Plots the graph
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    ax.set_yticks(midi_numbers)
    ax.set_yticklabels(notes)

    ax.set_xlim(0, max_time)
    ax.set_ylim(min(midi_numbers), max(midi_numbers) + 1)

    ax.grid(True)

    return fig
