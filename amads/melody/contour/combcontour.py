import numpy as np
from ...core.basics import Note, Score, Pitch
from ...algorithms.nnotes import nnotes
from ...pitch.ismonophonic import ismonophonic

def combcontour(score: Score):
    """
    Builds the Marvin & Laprade (1987) representation of melodic contour
    Given a score of n notes, combcontour will build an n x n matrix of
    ones and zeros. A one is inserted in the i,j-th entry if the pitch
    of note i is higher than the pitch of note j. A zero is inserted 
    otherwise. This matrix is a representation of melodic contour,
    preserving relative rather than specific pitch height info.
    
    Args:
        score (Score): The musical score to analyze

    Returns:
        c (np.ndarray): numpy ndarray (2D matrix) of ones and zeros representing melodic contour
    """
    

    a = nnotes(score)

    #if Score empty, return
    if a == 0: return
    
    #if Score is monophonic, return
    if not ismonophonic(score):
        print("Works only with monophonic input!")
        return
    
    #retrieve all the pitches
    p = [n.pitch.key_num for n in score.find_all(Note)]
    
    #create contour matrix
    c = np.zeros((a,a), int)
    for j in range(a):
        for k in range(a):
            c[j][k] = p[j] > p[k]
    
    return c
