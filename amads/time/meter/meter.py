
# TODO: meter.py is needed to estimate the meterings...
# However, what if we don't need to estimate the meterings? What then?

# meter.py uses autocorrelation to estimate the meters against a corpus of
# music with annotated meterings.

# dependencies:
# ofacorr
#   
# onsetfunc
#   onset (can be replaced with direct access)
#   melaccent

import math
import numpy as np
# meter function:
# inputs the score to calculate,
from amads.core.basics import Score, Note
from typing import List, Tuple

"""
function of = onsetfunc(nmat, accfunc);
! what the fuck does this mean?
% Sum of delta functions at onset times weighted by values obtained from ACCFUNC
% of = onsetfunc(nmat, <accfunc>);
%
% Input arguments:
%	NMAT = note matrix
%	ACCFUNC (optional) = accent function;
%
% Output:
%	OF = onset function
%
% Reference:
%	Brown, J. (1992). Determination of meter of musical scores by
%		autocorrelation. Journal of the acoustical society of America, 94 (4), 1953-1957.
% Comment: Auxiliary function that resides in private directory

NDIVS = 4; % four divisions per quater note
MAXLAG=8;
ob = onset(nmat);

if nargin==2
	acc=feval(accfunc,nmat);
else
	acc=ones(length(ob),1);
end

vlen = NDIVS*max([2*MAXLAG ceil(max(ob))+1]);
of = zeros(vlen,1);
ind = mod(round(ob*NDIVS),length(of))+1;
for k=1:length(ind)
	of(ind(k)) = of(ind(k))+acc(k);
end
"""

def onsetfunc(score: Score, accent_func = None) -> List[int]:
	# TODO: onset function here!
	ndivs = 4 # number of divisions per quarter note
	max_lag = 8
	target_score = None
	if accent_func:
		target_score = accent_func(score)
	else:
		target_score = score.flatten()

	onset_iter = (note.onset for note in target_score.find_all(Note))
	max_onset_note = math.ceil(max(onset_iter))
	# vlen
	wraparound = ndivs * max(2 * max_lag, max_onset_note + 1)

	onset_config = [0] * wraparound

	# what does this even mean semantically? (especially in the original matlab
	# ver.)
	# very confused what this function actually does...
	note_iter = target_score.find_all(Note)
	for idx, note in enumerate(note_iter):
		# ! be super careful about the in-built rounding policy differences
		# ! between matlab and python
		# accessor indices in matlab start from 1, but not in python
		target_idx = np.round(note.onset * ndivs) % wraparound
		onset_config[target_idx] += 1 if not accent_func else note.accent_val

	return onset_config

def meter(score: Score):
    assert 0