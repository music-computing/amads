"""
This is a Python wrapper for the R package 'melsim' (https://github.com/sebsilas/melsim).
This wrapper seeks to allow the user to easily interface with the melsim package using
the Score objects in AMADS.

Melsim is a package for computing similarity between melodies, and was written by
Sebastian Silas (https://sebsilas.com/). It is currently maintained by himself and
Klaus Frieler.
It is based on SIMILE, which was written by Daniel Müllensiefen and Klaus Frieler in 2003/2004.
Melsim is used to compare two or more melodies pairwise across a range of similarity measures.
Not all similarity measures are implemented in melsim, but the ones that are can be used in AMADS.

All of the following similarity measures are implemented and functional in melsim:
Please be aware that the names of the similarity measures are case-sensitive.

Num:        Name:
1           Jaccard
2       Kulczynski2
3            Russel
4   simple matching
5             Faith
6          Tanimoto
7              Dice
8            Mozley
9            Ochiai
10          Simpson
11           cosine
12          angular
13      correlation
14        Tschuprow
15           Cramer
16            Gower
17        Euclidean
18        Manhattan
19         supremum
20         Canberra
21            Chord
22         Geodesic
23             Bray
24          Soergel
25           Podani
26        Whittaker
27         eJaccard
28            eDice
29   Bhjattacharyya
30       divergence
31        Hellinger
32    edit_sim_utf8
33         edit_sim
34      Levenshtein
35          sim_NCD
36            const
37          sim_dtw

The following similarity measures are not currently functional in melsim:
1    count_distinct (set-based)
2          tversky (set-based)
3   braun_blanquet (set-based)
4        minkowski (vector-based)
5           ukkon (distribution-based)
6      sum_common (distribution-based)
7       distr_sim (distribution-based)
8   stringdot_utf8 (sequence-based)
9             pmi (special)
10       sim_emd (special)
"""

from functools import cache, wraps
from types import SimpleNamespace

from amads.core.basics import Note, Score
from amads.pitch.ismonophonic import ismonophonic
from amads.utils import check_python_package_installed

r_base_packages = ["base", "utils"]
r_cran_packages = ["tibble", "R6", "remotes"]

r_github_packages = ["melsim"]
github_repos = {
    "melsim": "sebsilas/melsim",
}

R = SimpleNamespace()


@cache
def load_melsim():
    check_python_package_installed("pandas")
    check_python_package_installed("rpy2")

    from rpy2.robjects import pandas2ri

    pandas2ri.activate()
    check_r_packages_installed()
    import_packages()


def requires_melsim(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        load_melsim()
        return func(*args, **kwargs)

    return wrapper


def check_r_packages_installed(install_missing: bool = False):
    from rpy2.robjects.packages import isinstalled

    for package in r_cran_packages + r_github_packages:
        if not isinstalled(package):
            if install_missing:
                install_r_package(package)
            else:
                raise ImportError(
                    f"Package '{package}' is required but not installed. "
                    "You can run install it by running the following command: "
                    "from amads.melody.similarity.melsim import install_dependencies; install_dependencies()"
                )


def install_r_package(package: str):
    from rpy2.robjects.packages import importr

    if package in r_cran_packages:
        print(f"Installing CRAN package '{package}'...")
        utils = importr("utils")
        utils.install_packages(package)
    elif package in r_github_packages:
        print(f"Installing GitHub package '{package}'...")
        remotes = importr("remotes")
        repo = github_repos[package]
        remotes.install_github(repo, upgrade="always")
    else:
        raise ValueError(f"Unknown package type for '{package}'")


def install_dependencies():
    check_r_packages_installed(install_missing=True)


def import_packages():
    from rpy2.robjects.packages import importr

    all_packages = r_base_packages + r_cran_packages + r_github_packages
    for package in all_packages:
        setattr(R, package, importr(package))


@requires_melsim
def get_similarity(melody_1: Score, melody_2: Score, method: str) -> float:
    """Calculate similarity between two melodies using the specified method.

    Parameters
    ----------
    melody_1 : Score
        First Score object containing a monophonic melody
    melody_2 : Score
        Second Score object containing a monophonic melody
    method : str
        Name of the similarity method to use

    Returns
    -------
    float
        Similarity value between the two melodies

    Raises
    ------
    ValueError
        If the number of melodies is not exactly two.

    Examples
    --------
    >>> from amads.core.basics import Score
    >>> # Create two simple melodies using from_melody
    >>> melody_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    >>> melody_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    >>> # Calculate similarity using Jaccard method
    >>> similarity = get_similarity(melody_1, melody_2, 'Jaccard')
    >>> 0 < similarity < 1
    True
    >>> # Verify that similarity between the same melody is 1
    >>> similarity = get_similarity(melody_1, melody_1, 'Jaccard')
    >>> similarity == 1
    True
    """

    r_load_melody(melody_1, "melody_1")
    r_load_melody(melody_2, "melody_2")
    load_similarity_measure(method)
    return r_get_similarity("melody_1", "melody_2", method)


loaded_melodies = {}


@requires_melsim
def r_load_melody(melody: Score, name: str):
    """Convert a Score to a format compatible with melsim R package.

    Args:
        melody: Score object containing a monophonic melody

    Returns:
        A melsim Melody object
    """
    import rpy2.robjects as ro
    from rpy2.robjects import FloatVector

    if name in loaded_melodies and loaded_melodies[name] is melody:
        return

    assert ismonophonic(melody)

    # Flatten the score to get notes in order
    flattened_score = melody.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract onset, pitch, duration for each note
    onsets = FloatVector([note.start for note in notes])
    pitches = FloatVector([note.keynum for note in notes])
    durations = FloatVector([note.duration for note in notes])

    # Create R tibble using tibble::tibble()
    tibble = R.tibble.tibble(onset=onsets, pitch=pitches, duration=durations)

    ro.r.assign(f"{name}", ro.r("melody_factory$new")(mel_data=tibble))
    loaded_melodies[name] = melody


@cache
def load_similarity_measure(method: str):
    import rpy2.robjects as ro

    ro.r.assign(
        f"{method}_sim",
        ro.r("sim_measure_factory$new")(
            name=method,
            full_name=method,
            transformation="pitch",
            parameters=ro.ListVector({}),
            sim_measure=method,
        ),
    )


@requires_melsim
def r_get_similarity(melody_1: str, melody_2: str, method: str) -> float:
    """
    Use the melsim R package to get the similarity between two or more melodies.
    This version of get_similarity is designed to be used alongside r_load_melody.
    The user should call r_load_melody for each melody they wish to compare, and then
    call r_get_similarity for each pair of melodies. This is more efficient than
    calling get_similarity for each pair of melodies, as the melodies are only loaded once,
    and stored in memory for each subsequent call. Similarity measures are already cached,
    making this the faster way to calculate similarity between multiple melodies.

    Args:
        melody_1: Name of the first melody. This should have already been passed to R
        (see r_load_melody).
        melody_2: Name of the second melody. This should have already been passed to R.
        method: Name of the similarity method.

    Returns:
        The similarity value for each of the melody comparisons
    """
    import rpy2.robjects as ro

    # Load the similarity measure
    load_similarity_measure(method)

    return float(
        ro.r(f"{melody_1}$similarity")(ro.r(f"{melody_2}"), ro.r(f"{method}_sim")).rx2(
            "sim"
        )[0]
    )
