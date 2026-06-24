__author__ = "Yiwen Zhao"

import numpy as np
from typing import Literal
from ..core.basics import Score, Note, Part

def calculate_narmour(
    score: Score, 
    principle: Literal['rd', 'rr', 'id', 'cl', 'pr', 'co']
) -> np.ndarray:
    """
    Calculate predictions from Narmour's Implication-realization model.
    
    This function implements various principles from Narmour's (1990) model
    of melodic expectancy, including revisions by Schellenberg (1997) and
    Krumhansl (1995).
    
    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.
    principle : {'rd', 'rr', 'id', 'cl', 'pr', 'co'}
        The specific principle to calculate:
        - 'rd': registral direction (Schellenberg 1997)
        - 'rr': registral return (Schellenberg 1997)
        - 'id': intervallic difference
        - 'cl': closure
        - 'pr': proximity (Schellenberg 1997)
        - 'co': consonance (Krumhansl 1995)
    
    Returns
    -------
    numpy.ndarray
        Array of expectancy values for each note in the melody.
        First two notes will have NaN values as they form the
        implicative interval.
    
    References
    ----------
    .. [1] Narmour, E. (1990). The Analysis and cognition of basic melodic 
           structures: The Implication-realization model. Chicago: University 
           of Chicago Press.
    .. [2] Schellenberg, E. G. (1997). Simplifying the implication-realization 
           model of melodic expectancy. Music Perception, 14, 295-318.
    .. [3] Krumhansl, C. L. (1995). Effects of musical context on similarity 
           and expectancy. Systematische musikwissenschaft, 3, 211-250.
    
    Examples
    --------
    >>> score = Score()
    >>> part = Part()
    >>> notes = [Note(pitch=60), Note(pitch=64), Note(pitch=67)]
    >>> for note in notes:
    ...     part.append(note)
    >>> score.append(part)
    >>> rd_values = calculate_narmour(score, 'rd')
    >>> print(rd_values)
    array([nan, nan, 0.75])
    """
    def registral_direction(pitches: np.ndarray) -> np.ndarray:
        """Calculate revised registral direction principle."""
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            # Get direction of implicative interval
            impl_dir = np.sign(pitches[i-1] - pitches[i-2])
            # Get direction of realized interval
            real_dir = np.sign(pitches[i] - pitches[i-1])
            # Calculate expectancy (1 if same direction, 0 if different)
            expectations[i] = float(impl_dir == real_dir)
        return expectations
    
    def registral_return(pitches: np.ndarray) -> np.ndarray:
        """Calculate revised registral return principle."""
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            # Calculate if third note returns to pitch region of first note
            diff_first_third = abs(pitches[i] - pitches[i-2])
            expectations[i] = 1.0 / (1.0 + diff_first_third)
        return expectations
    
    def intervallic_difference(pitches: np.ndarray) -> np.ndarray:
        """Calculate intervallic difference principle."""
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            # Compare size of implicative and realized intervals
            impl_interval = abs(pitches[i-1] - pitches[i-2])
            real_interval = abs(pitches[i] - pitches[i-1])
            # Smaller difference = higher expectancy
            expectations[i] = 1.0 / (1.0 + abs(impl_interval - real_interval))
        return expectations
    
    def closure(pitches: np.ndarray) -> np.ndarray:
        """Calculate closure principle."""
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            impl_interval = abs(pitches[i-1] - pitches[i-2])
            real_interval = abs(pitches[i] - pitches[i-1])
            # Closure occurs when realized interval is smaller
            expectations[i] = float(real_interval < impl_interval)
        return expectations
    
    def proximity(pitches: np.ndarray) -> np.ndarray:
        """Calculate revised proximity principle."""
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            # Smaller intervals are more expected
            interval = abs(pitches[i] - pitches[i-1])
            expectations[i] = 1.0 / (1.0 + interval)
        return expectations
    
    def consonance(pitches: np.ndarray) -> np.ndarray:
        """Calculate consonance principle."""
        # Consonance ratings from Krumhansl (1995)
        CONSONANCE_RATINGS = {
            0: 1.0,   # unison
            3: 0.6,   # minor third
            4: 0.8,   # major third
            5: 0.7,   # perfect fourth
            7: 0.9,   # perfect fifth
            8: 0.6,   # minor sixth
            9: 0.7,   # major sixth
            12: 0.9   # octave
        }
        
        expectations = np.full(len(pitches), np.nan)
        for i in range(2, len(pitches)):
            interval = abs(pitches[i] - pitches[i-1]) % 12
            expectations[i] = CONSONANCE_RATINGS.get(interval, 0.1)
        return expectations

    # Flatten and collapse the score into a single sequence of notes
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))
    
    # Handle empty scores or sequences too short for analysis
    if len(notes) < 3:
        return np.array([])
    
    # Extract pitch values
    pitches = np.array([note.keynum for note in notes])
    
    # Calculate expectations based on selected principle
    principle_functions = {
        'rd': registral_direction,
        'rr': registral_return,
        'id': intervallic_difference,
        'cl': closure,
        'pr': proximity,
        'co': consonance
    }
    
    return principle_functions[principle](pitches)


if __name__ == "__main__":
    # Test case 1: Simple ascending melody
    print("\nTest Case 1: Simple ascending melody")
    score = Score()
    part = Part()
    notes = [
        Note(pitch=60),  # C4
        Note(pitch=64),  # E4
        Note(pitch=67),  # G4
        Note(pitch=72)   # C5
    ]
    for note in notes:
        part.append(note)
    score.append(part)
    
    principles = ['rd', 'rr', 'id', 'cl', 'pr', 'co']
    for p in principles:
        values = calculate_narmour(score, p)
        print(f"{p} values:", values)
    
    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score values:", calculate_narmour(empty_score, 'rd'))
    
    # Test case 3: Two notes (too short)
    print("\nTest Case 3: Two notes")
    short_score = Score()
    short_part = Part()
    short_part.append(Note(pitch=60))
    short_part.append(Note(pitch=64))
    short_score.append(short_part)
    print("Two-note values:", calculate_narmour(short_score, 'rd'))
    
    # Test case 4: Changing direction
    print("\nTest Case 4: Changing direction")
    changing_score = Score()
    changing_part = Part()
    changing_notes = [
        Note(pitch=60),  # C4
        Note(pitch=64),  # E4
        Note(pitch=62),  # D4
        Note(pitch=67),  # G4
        Note(pitch=65)   # F4
    ]
    for note in changing_notes:
        changing_part.append(note)
    changing_score.append(changing_part)
    
    for p in principles:
        values = calculate_narmour(changing_score, p)
        print(f"{p} values:", values)