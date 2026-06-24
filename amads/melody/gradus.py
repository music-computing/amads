__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note, Part

def calculate_gradus(score: Score) -> float:
    """
    Calculate the degree of melodiousness (gradus suavitatis) according to Euler (1739).
    
    The gradus suavitatis measures melodic pleasantness based on the simplicity of 
    frequency ratios between successive notes. Lower values indicate higher melodiousness.
    The calculation decomposes intervals into frequency ratios and analyzes their prime factors.
    
    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.
    
    Returns
    -------
    float
        The degree of melodiousness value. Lower values indicate higher melodiousness.
        Returns 0 for empty scores or single notes.
    
    References
    ----------
    .. [1] Euler, L. (1739). Tentamen novae theoriae musicae.
    .. [2] Leman, M. (1995). Music and schema theory: Cognitive foundations of 
           systematic musicology. Berlin: Springer.
    
    Examples
    --------
    >>> score = Score()
    >>> part = Part()
    >>> notes = [Note(pitch=60), Note(pitch=64), Note(pitch=67)]  # C-E-G triad
    >>> for note in notes:
    ...     part.append(note)
    >>> score.append(part)
    >>> gradus_value = calculate_gradus(score)
    >>> print(gradus_value)
    8
    """
    def prime_factors(n: int) -> list:
        """Helper function to get prime factors of a number."""
        factors = []
        d = 2
        while n > 1:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
            if d * d > n:
                if n > 1:
                    factors.append(n)
                break
        return factors

    def calculate_interval_gradus(interval: int) -> int:
        """Calculate gradus value for a single interval."""
        # Frequency ratios for intervals within an octave
        interval_ratios = {
            0: (1, 1),    # unison
            1: (16, 15),  # minor second
            2: (9, 8),    # major second
            3: (6, 5),    # minor third
            4: (5, 4),    # major third
            5: (4, 3),    # perfect fourth
            6: (45, 32),  # tritone
            7: (3, 2),    # perfect fifth
            8: (8, 5),    # minor sixth
            9: (5, 3),    # major sixth
            10: (9, 5),   # minor seventh
            11: (15, 8),  # major seventh
            12: (2, 1)    # octave
        }
        
        interval = abs(interval) % 12  # normalize to within an octave
        numerator, denominator = interval_ratios[interval]
        
        # Get prime factors and calculate gradus
        factors = prime_factors(numerator) + prime_factors(denominator)
        return sum(p - 1 for p in factors)

    # Flatten the score and get all notes
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))
    
    # Handle empty scores or single notes
    if len(notes) < 2:
        return 0
    
    # Calculate intervals between consecutive notes
    intervals = [notes[i+1].keynum - notes[i].keynum 
                for i in range(len(notes)-1)]
    
    # Calculate total gradus
    total_gradus = sum(calculate_interval_gradus(i) for i in intervals)
    
    return total_gradus


if __name__ == "__main__":
    # Test case 1: C major triad (C-E-G)
    print("\nTest Case 1: C major triad")
    score = Score()
    part = Part()
    notes = [
        Note(pitch=60),  # C4
        Note(pitch=64),  # E4
        Note(pitch=67)   # G4
    ]
    for note in notes:
        part.append(note)
    score.append(part)
    
    gradus_value = calculate_gradus(score)
    print("Notes:", [note.name_with_octave for note in notes])
    print("Gradus value:", gradus_value)
    
    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score gradus:", calculate_gradus(empty_score))
    
    # Test case 3: Single note
    print("\nTest Case 3: Single note")
    single_note_score = Score()
    single_part = Part()
    single_part.append(Note(pitch=60))
    single_note_score.append(single_part)
    print("Single note gradus:", calculate_gradus(single_note_score))
    
    # Test case 4: Chromatic sequence
    print("\nTest Case 4: Chromatic sequence")
    chromatic_score = Score()
    chromatic_part = Part()
    for pitch in [60, 61, 62, 63, 64]:  # C4 to E4 chromatically
        chromatic_part.append(Note(pitch=pitch))
    chromatic_score.append(chromatic_part)
    print("Chromatic sequence gradus:", calculate_gradus(chromatic_score))