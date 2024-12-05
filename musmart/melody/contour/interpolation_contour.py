"""
Calculates the Interpolation Contour of a melody, along with related features, as
implemented in the FANTASTIC toolbox of Müllensiefen (2009).
"""

__author__ = "David Whyatt"

import numpy as np


def _find_contour_extrema(times: list[float], pitches: list[int]) -> list[int]:
    """Determine contour extremum notes (local minima and maxima, including endpoints).

    Excludes changing notes (notae cambiatae).

    Parameters
    ----------
    times : list[float]
        List of note onset times in seconds
    pitches : list[int]
        List of MIDI pitch values

    Returns
    -------
    numpy.ndarray
        Array of indices corresponding to extrema points in the melody
    """
    extrema_indices = []
    n = len(pitches)

    # Always include first and last notes
    extrema_indices.append(0)

    # Find local extrema
    for i in range(1, n-1):
        # Check previous and next notes
        prev_pitch = pitches[i-1]
        curr_pitch = pitches[i]
        next_pitch = pitches[i+1]

        # Skip changing notes (where adjacent pitches are equal)
        if prev_pitch == next_pitch:
            continue

        # Check if it's a peak or valley
        if ((prev_pitch < curr_pitch and next_pitch < curr_pitch) or
                (prev_pitch > curr_pitch and next_pitch > curr_pitch)):
            # Additional check for equal adjacent notes
            is_extremum = True
            if i > 1 and prev_pitch == curr_pitch:
                is_extremum = ((pitches[i-2] - curr_pitch) *
                             (next_pitch - curr_pitch) < 0)
            if i < n-2 and next_pitch == curr_pitch:
                is_extremum = ((prev_pitch - curr_pitch) *
                             (pitches[i+2] - curr_pitch) < 0)
            if is_extremum:
                extrema_indices.append(i)

    extrema_indices.append(n-1)  # Add last note
    return np.array(extrema_indices)


def calculate_interpolation_contour(times: list[float],
                                  pitches: list[int]) -> list[int]:
    """Calculate the interpolation contour [1] representation of a melody.

    Parameters
    ----------
    times : list[float]
        Array of onset times in seconds
    pitches : list[int]
        Array of pitch values

    Returns
    -------
    list[float]
        Array containing the interpolation contour representation

    Raises
    ------
    ValueError
        If times and pitches are not the same length

    Examples
    --------
    >>> calculate_interpolation_contour([0, 0.1, 0.2, 0.3], [60, 58, 64, 65])
    [-20.0, -20.0, -20.0, -20.0, -20.0, -20.0, -20.0, -20.0, -20.0, -20.0, 35.0,
    35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0,
    35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0]

    >>> calculate_interpolation_contour([0, 0.1, 0.2, 0.3], [60, 58, 64, 65, 65])
    Traceback (most recent call last):
        ...
    ValueError: Times and pitches must have the same length

    References
    ----------
    [1] Müllensiefen, D. (2009). FANTASTIC: Feature ANalysis Technology Accessing
    STatistics (In a Corpus): Technical Report v1.5
    https://www.doc.gold.ac.uk/isms/m4s/FANTASTIC_docs.pdf
    """
    if len(times) != len(pitches):
        raise ValueError("Times and pitches must have the same length")

    # Step 1 & 2: Find contour extrema
    extrema_indices = _find_contour_extrema(times, pitches)
    extrema_times = [times[i] for i in extrema_indices]
    extrema_pitches = [pitches[i] for i in extrema_indices]

    # Step 3: Calculate gradients
    gradients = np.diff(extrema_pitches) / np.diff(extrema_times)

    # Step 4: Calculate durations
    durations = np.diff(extrema_times)

    # Step 5: Remove durations below 0.05 seconds
    durations[durations < 0.05] = 0

    # Step 6: Create weighted gradients vector by repeating each gradient
    # proportional to its duration
    # Convert durations to integer number of samples (at 100Hz sampling rate)
    samples_per_duration = np.round(durations * 100).astype(int)
    interpolation_contour = np.repeat(gradients, samples_per_duration)
    return [float(x) for x in interpolation_contour]


def interpolation_contour_global_direction(
        interpolation_contour: list[float]) -> list[int]:
    """Calculate the global direction of the interpolation contour.

    Parameters
    ----------
    interpolation_contour : list[float]
        List of interpolation contour gradient values

    Returns
    -------
    list[int]
        List containing the signs (+1, 0, -1) of the gradient values in the contour

    Examples
    --------
    >>> contour = [-20.0, -20.0, 35.0, 35.0]
    >>> interpolation_contour_global_direction(contour)
    [-1, -1, 1, 1]

    >>> contour = [1, 2, 3, 4, 5]
    >>> interpolation_contour_global_direction(contour)
    [1, 1, 1, 1, 1]
    """
    # Calculate the signum of the interpolation contour using numpy's sign function
    global_direction = np.sign(interpolation_contour)

    return [int(x) for x in global_direction]


def interpolation_contour_mean_gradient(
        interpolation_contour: list[float]) -> float:
    """Calculate the absolute mean gradient of the interpolation contour.

    Parameters
    ----------
    interpolation_contour : list[float]
        List of interpolation contour gradient values

    Returns
    -------
    float
        Mean of the absolute gradient values

    Examples
    --------
    >>> contour = [-20.0, -20.0, 35.0, 35.0]
    >>> interpolation_contour_mean_gradient(contour)
    27.5

    >>> contour = [1, 2, 3, 4, 5]
    >>> interpolation_contour_mean_gradient(contour)
    3.0
    """
    return float(np.mean(np.abs(interpolation_contour)))


def interpolation_contour_gradients_std_dev(
        interpolation_contour: list[float]) -> float:
    """Calculate the standard deviation of the interpolation contour gradients.

    Parameters
    ----------
    interpolation_contour : list[float]
        List of interpolation contour gradient values

    Returns
    -------
    float
        Standard deviation of the gradient values

    Examples
    --------
    >>> contour = [-20.0, -20.0, 35.0, 35.0]
    >>> interpolation_contour_gradients_std_dev(contour)
    27.5

    >>> contour = [1, 2, 3, 4, 5]
    >>> interpolation_contour_gradients_std_dev(contour)
    1.4142...
    """
    return float(np.std(interpolation_contour))


def interpolation_contour_direction_changes(
        interpolation_contour: list[float]) -> float:
    """Calculate the ratio of direction changes in the interpolation contour.

    This measures the number of changes in contour direction relative to the number
    of interpolation lines (i.e. number of different gradient values).

    Parameters
    ----------
    interpolation_contour : list[float]
        List of interpolation contour gradient values

    Returns
    -------
    float
        Ratio of direction changes to total gradient changes (between 0 and 1)

    Examples
    --------
    >>> contour = [-20.0, -20.0, 35.0, 35.0, -10.0]
    >>> interpolation_contour_direction_changes(contour)
    2.0

    >>> contour = [1.0, 1.0, 1.0, 1.0]  # No direction changes
    >>> interpolation_contour_direction_changes(contour)
    0.0
    """
    # Get signs of all gradients
    signs = np.sign(interpolation_contour)

    # Count direction changes (where consecutive signs are different)
    direction_changes = np.sum(signs[:-1] != signs[1:])

    # Count total gradient changes (where consecutive values are different)
    total_changes = np.sum(
        interpolation_contour[:-1] != interpolation_contour[1:])

    # Avoid division by zero
    if total_changes == 0:
        return 0.0

    return float(direction_changes / total_changes)


def interpolation_contour_class(interpolation_contour: list[float]) -> str:
    """Classify an interpolation contour into gradient categories.

    The contour is sampled at 4 equally spaced points and each gradient is
    normalized and classified into one of 5 categories:

    - 'a': Strong downward (-2) - normalized gradient <= -1.45
    - 'b': Downward (-1) - normalized gradient between -1.45 and -0.45
    - 'c': Flat (0) - normalized gradient between -0.45 and 0.45
    - 'd': Upward (1) - normalized gradient between 0.45 and 1.45
    - 'e': Strong upward (2) - normalized gradient >= 1.45

    Parameters
    ----------
    interpolation_contour : list[float]
        List of interpolation contour values

    Returns
    -------
    str
        String of length 4 containing letters a-e representing the gradient
        categories at 4 equally spaced points in the contour

    Examples
    --------
    >>> contour = [-6.0, -2.0, 0.0, 2.0, 6.0]  # Down-flat-up pattern
    >>> interpolation_contour_class(contour)
    'abce'

    >>> contour = [6.0, 6.0, 6.0, 6.0]  # Consistently strong upward
    >>> interpolation_contour_class(contour)
    'eeee'
    """
    # Sample the contour at 4 equally spaced points
    # Get 4 equally spaced indices
    n = len(interpolation_contour)
    indices = np.linspace(0, n-1, 4, dtype=int)

    # Sample the contour at those indices
    sampled_points = [interpolation_contour[i] for i in indices]

    # Normalize the gradients to a norm where value of 1 corresponds to a semitone
    # change in pitch over 250ms. Given that base pitch and time units in
    # FANTASTIC are 1 second and 1 semitone respectively, just divide by 4
    norm_gradients = np.array(sampled_points) * 0.25

    classes = []
    for grad in norm_gradients:
        if grad <= -1.45:
            classes.append('a')  # strong down
        elif -1.45 < grad <= -0.45:
            classes.append('b')  # down
        elif -0.45 < grad < 0.45:
            classes.append('c')  # flat
        elif 0.45 <= grad < 1.45:
            classes.append('d')  # up
        else:
            classes.append('e')  # strong up

    return ''.join(classes)