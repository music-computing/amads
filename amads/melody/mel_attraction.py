__author__ = "Yiwen Zhao"

import numpy as np
from ..core.basics import Score, Note, Part

def get_pitch_space_weights(key: int, mode: str = 'major') -> dict:
    """
    Get the tonal pitch space weights for a given key based on Lerdahl's model.
    
    Parameters
    ----------
    key : int
        MIDI pitch number representing the tonic (e.g., 60 for C)
    mode : str, optional
        'major' or 'minor', by default 'major'
        
    Returns
    -------
    dict
        Dictionary mapping pitch classes (0-11) to their weights (1-5)
    """
    if mode == 'major':
        # Weights relative to tonic: [tonic, M2, M3, P4, P5, M6, M7]
        basic_weights = {0: 5, 2: 2, 4: 3, 5: 2, 7: 4, 9: 2, 11: 1}
    else:  # minor
        # Weights for natural minor
        basic_weights = {0: 5, 2: 2, 3: 3, 5: 2, 7: 4, 8: 2, 10: 1}
    
    # Map weights to actual pitch classes
    weights = {}
    tonic_pc = key % 12
    for interval, weight in basic_weights.items():
        pitch_class = (tonic_pc + interval) % 12
        weights[pitch_class] = weight
    
    # Fill in unspecified pitch classes
    for pc in range(12):
        if pc not in weights:
            weights[pc] = 1  # Lower weight for non-scale tones
            
    return weights

def calculate_attraction(note1: Note, note2: Note, weights: dict) -> float:
    """
    Calculate the melodic attraction between two notes using Lerdahl's model.
    
    Parameters
    ----------
    note1 : Note
        First note object
    note2 : Note
        Second note object
    weights : dict
        Dictionary of pitch space weights
        
    Returns
    -------
    float
        Attraction value between 0 and 1
    """
    pc1 = note1.keynum % 12
    pc2 = note2.keynum % 12
    
    w1 = weights[pc1]
    w2 = weights[pc2]
    
    distance = abs(note2.keynum - note1.keynum)
    
    if distance == 0:
        return 0  # Avoid division by zero
    
    # Lerdahl's attraction formula: (w2/w1) * (1/distance²)
    attraction = (w2/w1) * (1/distance**2)
    return attraction

def calculate_melodic_attraction(score: Score, key: int = None) -> list:
    """
    Calculate melodic attraction for each note according to Lerdahl's model.
    
    The model considers:
    1. Basic attraction between adjacent notes
    2. Influence of nearby notes within a window
    3. Direction of melodic motion
    
    Parameters
    ----------
    score : Score
        A Score object containing the melody to analyze
    key : int, optional
        MIDI pitch number representing the key. If None, first note is used as tonic
        
    Returns
    -------
    list
        List of attraction values between 0 and 1 for each note
    
    Examples
    --------
    >>> score = Score()
    >>> part = Part()
    >>> notes = [Note(pitch=60), Note(pitch=64), Note(pitch=67), Note(pitch=65)]
    >>> for note in notes:
    ...     part.append(note)
    >>> score.append(part)
    >>> attractions = calculate_melodic_attraction(score, key=60)
    >>> print(attractions)  # Example values
    [0.0, 0.45, 0.8, 0.6]
    """
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))
    
    if len(notes) < 2:
        return [0] * len(notes)
    
    # Infer key from first note if not provided
    if key is None:
        key = notes[0].keynum
    
    weights = get_pitch_space_weights(key)
    attractions = [0] * len(notes)
    
    # Calculate attraction for each note pair
    for i in range(len(notes)-1):
        # Basic attraction
        basic_attraction = calculate_attraction(notes[i], notes[i+1], weights)
        
        # Consider neighboring notes
        neighbor_attractions = []
        window_size = 3
        start = max(0, i-window_size)
        end = min(len(notes), i+window_size+1)
        
        for j in range(start, end):
            if j != i:
                neighbor_attraction = calculate_attraction(notes[i], notes[j], weights)
                neighbor_attractions.append(neighbor_attraction)
        
        avg_neighbor_attraction = (sum(neighbor_attractions) / len(neighbor_attractions)
                                 if neighbor_attractions else 0)
        
        # Consider melodic direction
        direction_factor = 1.0
        if i > 0:
            prev_direction = notes[i].keynum - notes[i-1].keynum
            next_direction = notes[i+1].keynum - notes[i].keynum
            if (prev_direction * next_direction > 0):
                direction_factor = 1.2  # Enhance same direction
            elif (prev_direction * next_direction < 0):
                direction_factor = 0.8  # Reduce direction changes
        
        # Combine factors
        attractions[i] = ((basic_attraction * 0.6 + 
                        avg_neighbor_attraction * 0.4) * direction_factor)
    
    # Normalize to 0-1 range
    if attractions:
        max_attraction = max(attractions)
        if max_attraction > 0:
            attractions = [a/max_attraction for a in attractions]
    
    return attractions


if __name__ == "__main__":
    # Test cases
    score = Score()
    part = Part()
    
    # Test case 1: Simple scale fragment
    print("\nTest Case 1: Simple scale fragment")
    notes = [
        Note(pitch=60),  # C4
        Note(pitch=62),  # D4
        Note(pitch=64),  # E4
        Note(pitch=65)   # F4
    ]
    
    for note in notes:
        part.append(note)
    score.append(part)
    
    attractions = calculate_melodic_attraction(score, key=60)
    print("Notes:", [note.name_with_octave for note in notes])
    print("Attraction values:", [f"{x:.2f}" for x in attractions])
    
    # Test case 2: Empty score
    print("\nTest Case 2: Empty score")
    empty_score = Score()
    print("Empty score attractions:", calculate_melodic_attraction(empty_score))
    
    # Test case 3: Single note
    print("\nTest Case 3: Single note")
    single_note_score = Score()
    single_part = Part()
    single_part.append(Note(pitch=60))
    single_note_score.append(single_part)
    print("Single note attraction:", calculate_melodic_attraction(single_note_score))