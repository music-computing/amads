"""
The 'algorithms' module contains algorithms that are not specific to a given
musical representation.  They are unlikely to stay here forever, we will probably
file them somewhere else in due course.
"""

from ..melody.boundary import boundary
from ..melody.segment_gestalt import segment_gestalt
from ..pitch.hz2midi import hz2midi
from ..pitch.ivdirdist1 import interval_direction_distribution_1

# from ..pitch.ivdirdist2 import interval_direction_distribution_2
from ..pitch.ivdist1 import interval_distribution_1
from ..pitch.ivdist2 import interval_distribution_2
from ..pitch.ivsizedist1 import interval_size_distribution_1

# from ..pitch.ivsizedist2 import interval_size_distribution_2
from ..pitch.pc_set_functions import *
from ..pitch.pcdist1 import pitch_class_distribution_1
from ..pitch.pcdist2 import pitch_class_distribution_2
from ..pitch.pitch_mean import pitch_mean
from ..polyphony.skylinemod import skyline
from ..time.durdist1 import duration_distribution_1
from ..time.durdist2 import duration_distribution_2
from ..time.meter.break_it_up import MetricalSplitter
from .complexity import lz77_complexity
from .entropy import entropy
from .nnotes import nnotes
from .scale import scale
