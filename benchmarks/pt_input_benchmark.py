# pt_input_benchmark.py -- experiments around partitura midi file input
# flake8: noqa E402,E303

import os
import sys
from typing import Optional

sys.path.append(os.path.dirname(__file__))
from timer import Timer

timer = Timer()

timer.init("import time")
timer.start()
from music21 import converter, note

timer.stop()
print("***************************")
print("music21 import time:")
timer.report()

# import partitura now that we have Timer
timer.start(reset=True)
import partitura as pt

timer.stop()
print("partitura import time (includes music21 import time):")
timer.report()
print("***************************")

from amads.io.m21_midi_import import music21_midi_import
from amads.io.pt_midi_import import partitura_midi_import
from amads.music import example

__author__ = "Roger B. Dannenberg"

MIDI_FILE = "midi/twochan.mid"  # example MIDI file
# MIDI_FILE = "sarabande.mid"  # example MIDI file

# As a baseline, let's see how long it takes to create a score with 1000 notes:

from amads.core.basics import Measure, Note, Part, Score, Staff


def test_m21_midi_import(m21print: Optional[bool] = False):
    """test the import of a MIDI file using Music21
    """
    midi_file = example.fullpath(MIDI_FILE)
    m21score = converter.parse(midi_file, format='midi')
    if m21print:
        for m21part in m21score:
            m21part.show('text')
    return m21score


def count_music21_notes():
    """Count the number of notes in a Music21 score"""
    m21score = test_m21_midi_import(m21print=False)
    return len(list(m21score.flatten().getElementsByClass(note.Note)))


def time_m21_midi_import(n) -> float:
    """Measure execution time for n calls and calculate the average"""
    average_time = timer.time_it(test_m21_midi_import,
                                 "music21 MIDI import time", n=n)
    note_count = count_music21_notes()
    average_time /= note_count
    print("Average time per note for music21 MIDI import:",
          f"{average_time:.6f} seconds")
    return average_time


def test_amads_m21_midi_import(m21print: Optional[bool] = False):
    """test the import of a MIDI file to AMADS using music21
    """
    midi_file = example.fullpath(MIDI_FILE)
    score = music21_midi_import(midi_file, m21print)
    if m21print:
        score.show()
    return score


def time_amads_m21_midi_import(n) -> float:
    """Measure execution time for n calls and calculate the average"""
    average_time = timer.time_it(test_amads_m21_midi_import,
                                 "AMADS music21 import time", n, [False])
    note_count = count_music21_notes()
    average_time /= note_count
    print("Average time per note for AMADS music21 import:",
          f"{average_time:.6f} seconds")
    return average_time


def generate_numbers(n):
    """Generator function to yield numbers from 0 to n-1."""
    for i in range(n):
        yield i


def time_yield_iteration():
    """Time the iteration over an array of 1000 numbers using yield."""
    # time with yield
    timer.init("list time")
    numbers = generate_numbers(1000)
    timer.start()
    for i in numbers:
        if i % 100 == 0:
            pass
    avg = timer.stop(report=True)
    print(f"Average time for each yield iteration: {avg:.6f} ms")

    # time without yield
    timer.init("list time")
    numbers = list(range(1000))
    timer.start()
    for i in numbers:
        if i % 100 == 0:
            pass
    avg = timer.stop(report=True)
    print(f"Average time for each list iteration: {avg:.6f} ms")


def create_score(n: int) -> Score:
    """create a score with n Notes - use quarter notes in 4/4 time
    """
    staff = Staff()
    score = Score(Part(staff))
    for i in range(n):
        if i % 4 == 0:  # time to create a new measure?
            measure = Measure(parent=staff, onset=n, duration=4)
        pitch = i % 24 + 48  # 2-octave chromatic scales
        Note(parent=measure, onset=n, duration=1, pitch=pitch)
    return score


def test_create_score():
    """test the creation of a score with 32 Notes
    """
    score = create_score(32)
    score.show()


def time_score_creation(nnotes: Optional[int] = 1000) -> float:
    """time how long it takes to create a score with n Notes

    Returns
    -------
    float
        time in seconds
    Parameters
    ----------
    n : int, optional
        number of notes to create, by default 1000
    """
    average_time = timer.time_it(create_score, "score creation time",
                                 n=20, args=[nnotes])
    average_time /= nnotes
    print(f"Average time to create one note: {average_time:.6f} seconds")
    return average_time


def test_pt_midi_import(show: Optional[bool] = False):
    """test the import of a MIDI file using partitura
    """
    midi_file = example.fullpath(MIDI_FILE)
    ptscore = pt.load_score_midi(midi_file)
    if show:
        for ptpart in ptscore:
            print(ptpart.pretty())
    return ptscore


def count_partitura_notes():
    """Count the number of notes in a Partitura score"""
    ptscore = test_pt_midi_import()
    return sum(len(part.notes) for part in ptscore.parts)


def time_pt_midi_import(n) -> float:
    """Measure execution time for n calls and calculate the average"""
    average_time = timer.time_it(test_pt_midi_import,
                                 "partitura MIDI import time", n=n)
    note_count = count_partitura_notes()
    average_time /= note_count
    print(f"Average time per note for Partitura MIDI import: {average_time:.6f} seconds")
    return average_time


def test_amads_pt_midi_import(show: Optional[bool] = False):
    """test the import of a MIDI file to AMADS using partitura
    """
    midi_file = example.fullpath(MIDI_FILE)
    ptscore = partitura_midi_import(midi_file, show)
    return ptscore


def time_amads_pt_midi_import(n) -> float:
    """Measure execution time for n calls and calculate the average"""
    print("Starting AMADS partitura MIDI import test")
    average_time = timer.time_it(test_amads_pt_midi_import,
                                 "AMADS MIDI import time", n)
    print("Finished AMADS partitura MIDI import test")
    note_count = count_partitura_notes()
    average_time /= note_count
    print(f"Average time per note for AMADS MIDI import: {average_time:.6f} seconds")
    return average_time


m21_notes = count_music21_notes()
print(f"Notes in Music21 score: {m21_notes}.")
test_m21_midi_import(m21print=False)  # test run the import function
t_m21_note = time_m21_midi_import(20)
print("***************************")
t_amads_m21_import = time_amads_m21_midi_import(20)
time_yield_iteration()
# test_create_score() # AMADS score creation with measures and notes
t_note_create = time_score_creation(300)  # 300 notes times 20 calls
print(f"Notes in Partitura score: {count_partitura_notes()}.")
test_pt_midi_import(show=False)  # test run the import function
# using 1 for n since Partitura is slow (for now)
t_pt_note = time_pt_midi_import(1)  # partitura import time
print(f"Notes in AMADS score: {count_partitura_notes()}.")
t_amads_pt_import = time_amads_pt_midi_import(1)

print(f"AMADS create time: {t_note_create:.6f} seconds per note")
print(f"Music21 import time: {t_m21_note:.6f} seconds per note")
print(f"AMADS m21 import time: {t_amads_m21_import:.6f} seconds per note")
print(f"Partitura import time: {t_pt_note:.6f} seconds per note")
print(f"AMADS pt import time: {t_amads_pt_import:.6f} seconds per note")
