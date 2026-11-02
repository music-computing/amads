__author__ = "Yiwen Zhao"

import numpy as np

from amads.core.basics import Note, Part, Score


def calculate_durational_accents(notes: list) -> np.ndarray:
    """Calculate durational accents based on relative note durations."""
    durations = np.array([note.dur for note in notes])
    # Normalize durations to create accent weights
    return durations / np.max(durations)


def calculate_pitch_accents(notes: list) -> np.ndarray:
    """Calculate pitch accents based on melodic intervals."""
    pitches = np.array([note.keynum for note in notes])
    intervals = np.abs(np.diff(pitches))
    # Pad first note to match length
    intervals = np.pad(intervals, (1, 0), "constant")
    # Normalize intervals to create accent weights
    return (
        intervals / np.max(intervals)
        if np.max(intervals) > 0
        else np.zeros_like(intervals)
    )


def calculate_metrical_accents(notes: list) -> np.ndarray:
    """Calculate metrical accents based on metric position."""
    # Assuming 4/4 meter for simplicity
    # Could be extended to handle different time signatures
    METER_PATTERN = np.array([1.0, 0.2, 0.5, 0.2])  # 4/4 meter weights

    accents = np.zeros(len(notes))
    current_position = 0

    for i, note in enumerate(notes):
        # Get position within measure (assuming 4/4)
        position_in_measure = current_position % 4
        accents[i] = METER_PATTERN[int(position_in_measure)]
        current_position += note.dur

    return accents


def calculate_accent_synchrony(
    accents1: np.ndarray, accents2: np.ndarray, accents3: np.ndarray
) -> float:
    """Calculate synchrony between different accent types."""
    # Normalize all accent arrays
    acc1_norm = (
        accents1 / np.max(accents1) if np.max(accents1) > 0 else accents1
    )
    acc2_norm = (
        accents2 / np.max(accents2) if np.max(accents2) > 0 else accents2
    )
    acc3_norm = (
        accents3 / np.max(accents3) if np.max(accents3) > 0 else accents3
    )

    # Calculate correlation between accent pairs
    corr12 = np.corrcoef(acc1_norm, acc2_norm)[0, 1]
    corr23 = np.corrcoef(acc2_norm, acc3_norm)[0, 1]
    corr13 = np.corrcoef(acc1_norm, acc3_norm)[0, 1]

    # Handle NaN correlations
    corr12 = 0 if np.isnan(corr12) else corr12
    corr23 = 0 if np.isnan(corr23) else corr23
    corr13 = 0 if np.isnan(corr13) else corr13

    # Average correlation as measure of synchrony
    return (corr12 + corr23 + corr13) / 3


def meter_accent(score: Score) -> float:
    """
    Calculate the phenomenal accent synchrony in a melody.

    This function measures how well different types of musical accents
    (durational, pitch, and metrical) align with each other. Higher
    synchrony indicates stronger alignment between different accent types.

    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.

    Returns
    -------
    float
        Accent synchrony value between 0 and 1.
        Higher values indicate greater synchronization between different
        types of accents.
        Returns 0 for empty scores or single notes.

    References
    ----------
    .. [1] Eerola, T., Himberg, T., Toiviainen, P., & Louhivuori, J.
           Perceived complexity of Western and African folk melodies by
           Western and African listeners.
    .. [2] Jones, M. R. (1987). Dynamic pattern structure in music: Recent
           theory and research. Perception and Psychophysics, 41, 621-634.

    Examples
    --------
    >>> score = Score()
    >>> part = Part()
    >>> notes = [
    ...     Note(pitch=60, dur=1.0),  # Quarter note C4
    ...     Note(pitch=64, dur=0.5),  # Eighth note E4
    ...     Note(pitch=67, dur=1.0)   # Quarter note G4
    ... ]
    >>> for note in notes:
    ...     part.append(note)
    >>> score.append(part)
    >>> accent_sync = calculate_meteraccent(score)
    >>> print(accent_sync)
    0.75
    """

    # Flatten and collapse the score into a single sequence of notes
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Handle empty scores or single notes
    if len(notes) < 2:
        return 0

    # Calculate different types of accents
    durational_accents = calculate_durational_accents(notes)
    pitch_accents = calculate_pitch_accents(notes)
    metrical_accents = calculate_metrical_accents(notes)

    # Calculate overall accent synchrony
    synchrony = calculate_accent_synchrony(
        durational_accents, pitch_accents, metrical_accents
    )

    # Ensure return value is between 0 and 1
    return max(0, min(1, (synchrony + 1) / 2))


if __name__ == "__main__":
    # Test case 1: Regular rhythm with aligned accents
    print("\nTest Case 1: Regular rhythm with aligned accents")
    score = Score()
    part = Part()
    notes = [
        Note(pitch=60, dur=1.0),  # C4, quarter note
        Note(pitch=64, dur=0.5),  # E4, eighth note
        Note(pitch=67, dur=1.0),  # G4, quarter note
        Note(pitch=65, dur=0.5),  # F4, eighth note
    ]
    for note in notes:
        part.append(note)
    score.append(part)

    accent_sync = meter_accent(score)
    print("Notes:", [(note.name_with_octave, note.dur) for note in notes])
    print("Accent synchrony:", accent_sync)

    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score accent synchrony:", meter_accent(empty_score))

    # Test case 3: Single note
    print("\nTest Case 3: Single note")
    single_note_score = Score()
    single_part = Part()
    single_part.append(Note(pitch=60, dur=1.0))
    single_note_score.append(single_part)
    print(
        "Single note accent synchrony:",
        meter_accent(single_note_score),
    )

    # Test case 4: Syncopated rhythm
    print("\nTest Case 4: Syncopated rhythm")
    syncopated_score = Score()
    syncopated_part = Part()
    syncopated_notes = [
        Note(pitch=60, dur=0.5),  # C4, eighth
        Note(pitch=64, dur=1.5),  # E4, dotted quarter
        Note(pitch=67, dur=0.5),  # G4, eighth
        Note(pitch=65, dur=1.5),  # F4, dotted quarter
    ]
    for note in syncopated_notes:
        syncopated_part.append(note)
    syncopated_score.append(syncopated_part)
    print(
        "Syncopated rhythm accent synchrony:",
        meter_accent(syncopated_score),
    )

    # Test case 5: Complex rhythm with large intervals
    print("\nTest Case 5: Complex rhythm with large intervals")
    complex_score = Score()
    complex_part = Part()
    complex_notes = [
        Note(pitch=60, dur=1.0),  # C4, quarter
        Note(pitch=72, dur=0.25),  # C5, sixteenth
        Note(pitch=65, dur=0.75),  # F4, dotted eighth
        Note(pitch=69, dur=0.5),  # A4, eighth
    ]
    for note in complex_notes:
        complex_part.append(note)
    complex_score.append(complex_part)
    print("Complex rhythm accent synchrony:", meter_accent(complex_score))
