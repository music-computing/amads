"""Ports `pianoroll` Function

Original Doc: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6e06906ca1ba0bf0ac8f2cb1a929f3be95eeadfa#page=82
"""

from typing import cast

import matplotlib.pyplot as plt
from matplotlib import figure, patches

from amads.core.basics import Note, Part, Score
from amads.core.pitch import Pitch


def pianoroll(
    score: Score,
    title: str = "Piano Roll",
    y_label: str = "name",
    x_label: str = "quarter",
    color: str = "skyblue",
    accidental: str = "sharp",
    show: bool = True,
) -> figure.Figure:
    """Converts a Score to a piano roll display of a musical score.

    Parameters
    ----------
    score : Score
        The musical score to display
    title : str, optional
        The title of the plot. Defaults to "Piano Roll".
    y_label : str, optional
        Determines whether the y-axis is
        labeled with note names or MIDI numbers.
        Valid Input: 'name' (default) or 'num'.
    x_label : str, optional
        Determines whether the x-axis is labeled with quarters or
        seconds. Valid input: 'quarter' (default) or 'sec'.
    color : str, optional
        The color of the note rectangles. Defaults to 'skyblue'.
    accidental : str, optional
        Determines whether the y-axis is
        labeled with sharps or flats. Only useful if argument
        y_label is 'name'. Raises exception on inputs that's not
        'sharp', 'flat', or 'both'. Defaults to 'sharp', which is
        what is done in miditoolbox. 'both' means use AMADS defaults
        which are C#, Eb, F#, G#, Bb.
    show : bool, optional
        If True (default), the plot is displayed.

    Returns
    -------
    Figure
        A matplotlib.figure.Figure of a pianoroll diagram.

    Raises
    ------
    ValueError
        If there are invalid input arguments
    """

    # remove ties and make a sorted list of all notes:
    score = score.flatten(collapse=True)
    # Check for correct x_label input argument
    if x_label != "quarter" and x_label != "sec":
        raise ValueError("Invalid x_label type")

    # Check for correct accidental input argument
    if accidental != "sharp" and accidental != "flat" and accidental != "both":
        raise ValueError("Invalid accidental type")

    fig, ax = plt.subplots()

    min_note, max_note = 127.0, 0.0
    max_time = 1  # plot at least 1 second or beat
    # now score has one part that is all notes
    for note in cast(Part, next(score.find_all(Part))).content:
        note = cast(Note, note)
        onset_time = note.onset
        offset_time = note.offset
        pitch = note.key_num - 0.5  # to center note rectangle

        # Conditionally converts beat to sec
        if x_label == "sec" and score.units_are_quarters:
            onset_time = score.time_map.quarter_to_time(onset_time)
            offset_time = score.time_map.quarter_to_time(offset_time)
        elif x_label == "quarter" and score.units_are_seconds:
            onset_time = score.time_map.time_to_quarter(onset_time)
            offset_time = score.time_map.time_to_quarter(offset_time)
        # Stores min and max note for y_axis labeling
        if pitch < min_note:
            min_note = pitch
        if pitch > max_note:
            max_note = pitch

        # Stores max note start time + note duration for x_axis limit
        if offset_time > max_time:
            max_time = offset_time

        # Draws the note
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
            y_label = "MIDI Key (Pitch) Number"
        case "name":
            if accidental == "both":
                accidental = "default"  # for simplest_enharmonic
            notes = [
                Pitch(mn).simplest_enharmonic(accidental).name_with_octave
                for mn in midi_numbers
            ]
            y_label = "Pitch Name"
        case _:
            raise ValueError("Invalid y_label type")

    # Plots the graph
    ax.set_title(title)

    ax.set_xlabel("Quarters" if x_label == "quarter" else "Seconds")
    ax.set_ylabel(y_label)

    ax.set_yticks(midi_numbers)
    ax.set_yticklabels([str(note) for note in notes])

    ax.set_xlim(0, max_time)
    ax.set_ylim(min(midi_numbers), max(midi_numbers) + 1)

    ax.grid(True)

    if show:
        plt.show()

    return fig
