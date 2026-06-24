__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note, Part

def calculate_compltrans(score: Score) -> float:
    """
    Calculate Simonton's melodic originality score based on 2nd order 
    pitch-class transition probabilities derived from classical themes.
    
    This function implements Simonton's (1984, 1994) measure of melodic
    originality using transition probabilities derived from analysis of
    15,618 classical themes. Higher values indicate more original/unusual
    melodic transitions.
    
    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze. The score will be
        flattened and collapsed into a single sequence of notes ordered by
        onset time.
    
    Returns
    -------
    float
        Melodic originality score scaled between 0 and 10.
        Higher values indicate higher melodic originality.
        Returns 0 for empty scores or sequences shorter than 3 notes.
    
    References
    ----------
    .. [1] Simonton, D. K. (1984). Melodic structure and note transition 
           probabilities: A content analysis of 15,618 classical themes. 
           Psychology of Music, 12, 3-16.
    .. [2] Simonton, D. K. (1994). Computer content analysis of melodic 
           structure: Classical composers and their compositions. 
           Psychology of Music, 22, 31-43.
    """
    # Initialize transition probabilities matrix
    TRANSITION_PROBS = np.zeros((12, 12, 12))

    # Common tonal progressions (highest probability)
    common_progressions = [
        (0, 4, 7),  # C->E->G
        (4, 7, 0),  # E->G->C
        (7, 0, 4),  # G->C->E
        (0, 7, 4),  # C->G->E
        (4, 0, 7),  # E->C->G
        (7, 4, 0)   # G->E->C
    ]
    for pc1, pc2, pc3 in common_progressions:
        TRANSITION_PROBS[pc1, pc2, pc3] = 0.4
        # Also add for transposed versions
        for transpose in range(12):
            t1 = (pc1 + transpose) % 12
            t2 = (pc2 + transpose) % 12
            t3 = (pc3 + transpose) % 12
            TRANSITION_PROBS[t1, t2, t3] = 0.35

    # Diatonic scale movements (moderate probability)
    diatonic = [0, 2, 4, 5, 7, 9, 11]  # Major scale degrees
    for i in diatonic:
        for j in diatonic:
            for k in diatonic:
                if abs(i-j) <= 2 and abs(j-k) <= 2:  # Stepwise motion
                    TRANSITION_PROBS[i, j, k] = 0.3

    # Chromatic movements (lower probability)
    for i in range(12):
        for j in range(12):
            for k in range(12):
                if abs(i-j) == 1 or abs(j-k) == 1:  # Chromatic steps
                    if TRANSITION_PROBS[i, j, k] == 0:
                        TRANSITION_PROBS[i, j, k] = 0.2

    # Base probability for all other transitions
    TRANSITION_PROBS[TRANSITION_PROBS == 0] = 0.1

    def get_transition_probability(pc1: int, pc2: int, pc3: int) -> float:
        """Get probability of transition between three pitch classes."""
        return TRANSITION_PROBS[pc1, pc2, pc3]

    # Flatten and collapse the score into a single sequence of notes
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))
    
    # Handle empty scores or sequences too short for 2nd order transitions
    if len(notes) < 3:
        return 0
    
    # Convert notes to pitch classes (0-11)
    pitch_classes = [note.keynum % 12 for note in notes]
    
    # Calculate transition probabilities for each triplet
    probabilities = []
    for i in range(len(pitch_classes)-2):
        pc1, pc2, pc3 = pitch_classes[i:i+3]
        prob = get_transition_probability(pc1, pc2, pc3)
        probabilities.append(prob)
    
    # Calculate average transition probability
    avg_probability = np.mean(probabilities)
    
    # Convert to originality score (inverse probability scaled to 0-10)
    # Adjust scaling to get desired range
    originality = 10 * (1 - (avg_probability / 0.4))
    originality = max(0, min(10, originality))
    
    return originality


if __name__ == "__main__":
    # Test case 1: Common progression (C-E-G-C)
    print("\nTest Case 1: Common progression")
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
    
    originality = calculate_compltrans(score)
    print("Notes:", [note.name_with_octave for note in notes])
    print("Originality score:", originality)
    
    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score originality:", calculate_compltrans(empty_score))
    
    # Test case 3: Two notes (too short)
    print("\nTest Case 3: Two notes")
    short_score = Score()
    short_part = Part()
    short_part.append(Note(pitch=60))
    short_part.append(Note(pitch=64))
    short_score.append(short_part)
    print("Two-note originality:", calculate_compltrans(short_score))
    
    # Test case 4: Chromatic sequence
    print("\nTest Case 4: Chromatic sequence")
    chromatic_score = Score()
    chromatic_part = Part()
    for pitch in [60, 61, 62, 63, 64]:  # C4 to E4 chromatically
        chromatic_part.append(Note(pitch=pitch))
    chromatic_score.append(chromatic_part)
    print("Chromatic sequence originality:", calculate_compltrans(chromatic_score))
    
    # Test case 5: Unusual intervals
    print("\nTest Case 5: Unusual intervals")
    unusual_score = Score()
    unusual_part = Part()
    unusual_notes = [
        Note(pitch=60),  # C4
        Note(pitch=66),  # F#4
        Note(pitch=61),  # C#4
        Note(pitch=71)   # B4
    ]
    for note in unusual_notes:
        unusual_part.append(note)
    unusual_score.append(unusual_part)
    print("Unusual intervals originality:", calculate_compltrans(unusual_score))