import numpy as np
from ..core.basics import Note, Score
from ..algorithms.nnotes import nnotes

def concur(score: Score, threshold: float = None):
    """

    
    Args:
        score (Score): The musical score to analyze
        threshold (float): (optional) value for threshold for concurrent
                            onsets default value is +/- 0.2 beats

    Returns:
        c (float): number representing the proportion of concurrent onsets
        
        
    Example:
        concur(score, 0.25)
    """
    
    a = nnotes(score)
    #if score is empty, return
    if a == 0: return; end
    
    #if threshold is not provided, set it to 0.2
    if threshold is None: threshold = 0.2

    #get unique onset times
    
    all_onsets = np.array([n.onset for n in score.find_all(Note)])
    unique_onsets = np.unique(all_onsets)
    
    s = 0
    for z in unique_onsets:
        num_concurrent = np.sum((all_onsets >= z - threshold) & (all_onsets <= z + threshold)) - 1
        s += num_concurrent

    #calculate the proportion of concurrent onsets
    c = s/a

    return float(c)
