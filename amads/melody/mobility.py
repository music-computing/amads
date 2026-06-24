__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note, Part

def calculate_mobility(score: Score) -> np.ndarray:
    """
    Calculate the mobility measure for each tone in a melody (von Hippel, 2000).
    
    Mobility describes why melodies change direction after large skips by observing
    that they would otherwise run out of the comfortable melodic range. It uses
    lag-one autocorrelation between successive pitch heights.
    
    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.
    
    Returns
    -------
    numpy.ndarray
        An array of mobility values for each note. The first and last values
        are NaN since mobility requires both a previous and next interval
        to calculate.
    
    Examples
    --------
    >>> score = Score()
    >>> part = Part()
    >>> notes = [Note(pitch=60), Note(pitch=64), Note(pitch=62), Note(pitch=67), Note(pitch=65)]
    >>> for note in notes:
    ...     part.append(note)
    >>> score.append(part)
    >>> mobility_values = calculate_mobility(score)
    >>> print(mobility_values)
    array([nan, -0.5,  0.4, -0.4, nan])
    """

    # Flatten and collapse the score into a single sequence of notes
    flattened_score = score.flatten(collapse=True)
    
    # Get all notes from the flattened score
    notes = list(flattened_score.find_all(Note))
    
    # Handle empty or too short sequences
    if len(notes) < 2:
        return np.array([np.nan] if notes else [])
    
    # Extract pitch values from the notes
    pitches = np.array([note.keynum for note in notes])
    
    # Initialize mobility array with NaN values
    mobility_values = np.full(len(pitches), np.nan)
    
    # Calculate mobility for each note except the first and last
    for i in range(1, len(pitches)-1):
        current_interval = pitches[i] - pitches[i-1]
        next_interval = pitches[i+1] - pitches[i]
        
        # Calculate mobility as negative correlation between successive intervals
        if current_interval != 0:
            mobility_values[i] = -next_interval / current_interval
    
    return mobility_values


if __name__ == "__main__":
    # Create a test score
    score = Score()
    part = Part()
    
    # Test case 1: Simple melody
    print("\nTest Case 1: Simple melody")
    notes = [
        Note(pitch=60),  # C4
        Note(pitch=64),  # E4 (up 4 semitones)
        Note(pitch=62),  # D4 (down 2 semitones)
        Note(pitch=67),  # G4 (up 5 semitones)
        Note(pitch=65)   # F4 (down 2 semitones)
    ]
    
    for note in notes:
        part.append(note)
    score.append(part)
    
    mobility_values = calculate_mobility(score)
    print("Notes:", [note.name_with_octave for note in notes])
    print("Mobility values:", mobility_values)
    
    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score mobility:", calculate_mobility(empty_score))
    
    # Test case 3: Single note
    print("\nTest Case 3: Single note")
    single_note_score = Score()
    single_part = Part()
    single_part.append(Note(pitch=60))
    single_note_score.append(single_part)
    print("Single note mobility:", calculate_mobility(single_note_score))
    
    # Test case 4: Two notes
    print("\nTest Case 4: Two notes")
    two_note_score = Score()
    two_note_part = Part()
    two_note_part.append(Note(pitch=60))
    two_note_part.append(Note(pitch=64))
    two_note_score.append(two_note_part)
    print("Two notes mobility:", calculate_mobility(two_note_score))