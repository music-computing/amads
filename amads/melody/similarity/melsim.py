"""
This is a Python wrapper for the R package 'melsim' (https://github.com/sebsilas/melsim).
This wrapper allows the user to easily interface with the melsim package using the AMADS Score object.
Melsim is a package for computing similarity between melodies, and is being developed by
Sebastian Silas (https://sebsilas.com/) and Klaus Frieler
(https://www.aesthetics.mpg.de/en/the-institute/people/klaus-frieler.html).
Melsim is based on SIMILE, which was written by Daniel Müllensiefen and Klaus Frieler in 2003/2004.
This package is used to compare two or more melodies pairwise across a range of similarity measures.
Not all similarity measures are implemented in melsim, but the ones that are can be used here.
All of the following similarity measures are implemented and functional in melsim:
Please be aware that the names of the similarity measures are case-sensitive.
Num:        Name:
1           Jaccard
2       Kulczynski2
3            Russel
4             Faith
5          Tanimoto
6              Dice
7            Mozley
8            Ochiai
9            Simpson
10           cosine
11          angular
12      correlation
13        Tschuprow
14           Cramer
15            Gower
16        Euclidean
17        Manhattan
18         supremum
19         Canberra
20            Chord
21         Geodesic
22             Bray
23          Soergel
24           Podani
25        Whittaker
26         eJaccard
27            eDice
28   Bhjattacharyya
29       divergence
30        Hellinger
31    edit_sim_utf8
32         edit_sim
33      Levenshtein
34          sim_NCD
35            const
36          sim_dtw
The following similarity measures are not currently functional in melsim:
1    count_distinct (set-based)
2          tversky (set-based)
3   simple matching
4   braun_blanquet (set-based)
5        minkowski (vector-based)
6           ukkon (distribution-based)
7      sum_common (distribution-based)
8       distr_sim (distribution-based)
9   stringdot_utf8 (sequence-based)
10            pmi (special)
11       sim_emd (special)
Further to the similarity measures, melsim allows the user to specify which domain the
similarity should be calculated for. This is referred to as a "transformation" in melsim,
and all of the following transformations are implemented and functional:
Num:        Name:
1           pitch
2           int
3           fuzzy_int
4           parsons
5           pc
6           ioi_class
7           duration_class
8           int_X_ioi_class
9           implicit_harmonies
The following transformations are not currently functional in melsim:
Num:        Name:
1           ioi
2           phrase_segmentation
"""

import json
import math
import subprocess
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential
from tqdm import tqdm

r_base_packages = ["base", "utils"]
r_cran_packages = [
    "tibble",
    "R6",
    "remotes",
    "dplyr",
    "magrittr",
    "proxy",
    "purrr",
    "purrrlyr",
    "tidyr",
    "yaml",
    "stringr",
    "emdist",
    "dtw",
    "ggplot2",
    "cba",
]
r_github_packages = ["melsim"]
github_repos = {
    "melsim": "sebsilas/melsim",
}


def check_r_packages_installed(install_missing: bool = False, n_retries: int = 3):
    """Check if required R packages are installed."""
    # Create R script to check package installation using base R only
    check_script = """
    packages <- c({packages})
    missing <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
    if (length(missing) > 0) {{
        cat(paste0('"', missing, '"', collapse = ","))
    }} else {{
        cat("")
    }}
    """

    # Format package list
    packages_str = ", ".join([f'"{p}"' for p in r_cran_packages + r_github_packages])
    check_script = check_script.format(packages=packages_str)

    # Run R script
    try:
        result = subprocess.run(
            ["Rscript", "-e", check_script], capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()

        # Parse the output - if empty, no missing packages
        if not output:
            missing_packages = []
        else:
            # Parse comma-separated quoted strings
            missing_packages = [pkg.strip('"') for pkg in output.split(",")]

        if missing_packages:
            if install_missing:
                for package in missing_packages:
                    try:
                        for attempt in Retrying(
                            stop=stop_after_attempt(n_retries),
                            wait=wait_exponential(multiplier=1, min=1, max=10),
                        ):
                            with attempt:
                                install_r_package(package)
                    except RetryError as e:
                        raise RuntimeError(
                            f"Failed to install R package '{package}' after {n_retries} attempts. "
                            "See above for the traceback."
                        ) from e
            else:
                raise ImportError(
                    f"Packages {missing_packages} are required but not installed. "
                    "You can install them by running: install_dependencies()"
                )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error checking R packages: {e.stderr}")


def install_r_package(package: str):
    """Install an R package."""
    if package in r_cran_packages:
        print(f"Installing CRAN package '{package}'...")
        install_script = f"""
        utils::chooseCRANmirror(ind=1)
        utils::install.packages("{package}", dependencies=TRUE)
        """
        subprocess.run(["Rscript", "-e", install_script], check=True)
    elif package in r_github_packages:
        print(f"Installing GitHub package '{package}'...")
        repo = github_repos[package]
        install_script = f"""
        if (!requireNamespace("remotes", quietly = TRUE)) {{
            utils::install.packages("remotes")
        }}
        remotes::install_github("{repo}", upgrade="always", dependencies=TRUE)
        """
        subprocess.run(["Rscript", "-e", install_script], check=True)
    else:
        raise ValueError(f"Unknown package type for '{package}'")


def install_dependencies():
    """Install all required R packages."""
    # Check which packages need to be installed using base R only
    check_script = """
    packages <- c({packages})
    missing <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
    if (length(missing) > 0) {{
        cat(paste0('"', missing, '"', collapse = ","))
    }} else {{
        cat("")
    }}
    """

    # Check CRAN packages
    packages_str = ", ".join([f'"{p}"' for p in r_cran_packages])
    check_script_cran = check_script.format(packages=packages_str)

    try:
        result = subprocess.run(
            ["Rscript", "-e", check_script_cran],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()

        # Parse the output - if empty, no missing packages
        if not output:
            missing_cran = []
        else:
            # Parse comma-separated quoted strings
            missing_cran = [pkg.strip('"') for pkg in output.split(",")]

        if missing_cran:
            print("Installing missing CRAN packages...")
            cran_script = f"""
            utils::chooseCRANmirror(ind=1)
            utils::install.packages(c({", ".join([f'"{p}"' for p in missing_cran])}), dependencies=TRUE)
            """
            subprocess.run(["Rscript", "-e", cran_script], check=True)
        else:
            print("Skipping install: All CRAN packages are already installed.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error checking CRAN packages: {e.stderr}")

    # Check GitHub packages
    packages_str = ", ".join([f'"{p}"' for p in r_github_packages])
    check_script_github = check_script.format(packages=packages_str)

    try:
        result = subprocess.run(
            ["Rscript", "-e", check_script_github],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()

        # Parse the output - if empty, no missing packages
        if not output:
            missing_github = []
        else:
            # Parse comma-separated quoted strings
            missing_github = [pkg.strip('"') for pkg in output.split(",")]

        if missing_github:
            print("Installing missing GitHub packages...")
            for package in missing_github:
                repo = github_repos[package]
                print(f"Installing {package} from {repo}...")
                install_script = f"""
                if (!requireNamespace("remotes", quietly = TRUE)) {{
                    utils::install.packages("remotes")
                }}
                remotes::install_github("{repo}", upgrade="always", dependencies=TRUE)
                """
                subprocess.run(["Rscript", "-e", install_script], check=True)
        else:
            print("Skipping install: All GitHub packages are already installed.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error checking GitHub packages: {e.stderr}")

    print("All dependencies are installed and up to date.")


def check_python_package_installed(package: str):
    """Check if a Python package is installed."""
    try:
        __import__(package)
    except ImportError:
        raise ImportError(
            f"Package '{package}' is required but not installed. "
            f"Please install it using pip: pip install {package}"
        )


# Valid similarity measures and transformations as listed in the module docstring
VALID_METHODS = [
    "Jaccard",
    "Kulczynski2",
    "Russel",
    "Faith",
    "Tanimoto",
    "Dice",
    "Mozley",
    "Ochiai",
    "Simpson",
    "cosine",
    "angular",
    "correlation",
    "Tschuprow",
    "Cramer",
    "Gower",
    "Euclidean",
    "Manhattan",
    "supremum",
    "Canberra",
    "Chord",
    "Geodesic",
    "Bray",
    "Soergel",
    "Podani",
    "Whittaker",
    "eJaccard",
    "eDice",
    "Bhjattacharyya",
    "divergence",
    "Hellinger",
    "edit_sim_utf8",
    "edit_sim",
    "Levenshtein",
    "sim_NCD",
    "const",
    "sim_dtw",
]

VALID_TRANSFORMATIONS = [
    "pitch",
    "int",
    "fuzzy_int",
    "parsons",
    "pc",
    "ioi_class",
    "duration_class",
    "int_X_ioi_class",
    "implicit_harmonies",
]


def validate_method(method: str):
    """Validate that the similarity method is supported."""
    if method not in VALID_METHODS:
        raise ValueError(
            f"Invalid method '{method}'. Valid methods are: {', '.join(VALID_METHODS)}"
        )


def validate_transformation(transformation: str):
    """Validate that the transformation is supported."""
    if transformation not in VALID_TRANSFORMATIONS:
        raise ValueError(
            f"Invalid transformation '{transformation}'. Valid transformations are: {', '.join(VALID_TRANSFORMATIONS)}"
        )


def get_similarity(melody_1, melody_2, method: str, transformation: str) -> float:
    """Calculate similarity between two Score objects using the specified method.
    Parameters
    ----------
    melody_1 : Score
        First Score object containing a monophonic melody
    melody_2 : Score
        Second Score object containing a monophonic melody
    method : str
        Name of the similarity method to use from the list in the module docstring.
    transformation : str
        Name of the transformation to use from the list in the module docstring.
    Returns
    -------
    float
        Similarity value between the two melodies
    Examples
    --------
    >>> from amads.core.basics import Score
    >>> # Create two simple melodies using from_melody
    >>> melody_1 = Score.from_melody(pitches=[60, 62, 64, 65], durations=1.0)
    >>> melody_2 = Score.from_melody(pitches=[60, 62, 64, 67], durations=1.0)
    >>> # Calculate similarity using Jaccard method
    >>> similarity = get_similarity(melody_1, melody_2, 'Jaccard', 'pitch')
    """
    # Validate inputs
    validate_method(method)
    validate_transformation(transformation)

    # Convert Score objects to arrays
    pitches1, starts1, ends1 = score_to_arrays(melody_1)
    pitches2, starts2, ends2 = score_to_arrays(melody_2)

    # Pass lists directly to _get_similarity
    return _get_similarity(
        pitches1, starts1, ends1, pitches2, starts2, ends2, method, transformation
    )


def _get_similarity(
    melody1_pitches: List[float],
    melody1_starts: List[float],
    melody1_ends: List[float],
    melody2_pitches: List[float],
    melody2_starts: List[float],
    melody2_ends: List[float],
    method: str,
    transformation: str,
) -> float:
    """Calculate similarity between two melodies using the specified method.
    Parameters
    ----------
    melody1_pitches : List[float]
        Pitch values for the first melody
    melody1_starts : List[float]
        Start times for the first melody
    melody1_ends : List[float]
        End times for the first melody
    melody2_pitches : List[float]
        Pitch values for the second melody
    melody2_starts : List[float]
        Start times for the second melody
    melody2_ends : List[float]
        End times for the second melody
    method : str
        Name of the similarity method to use
    transformation : str
        Name of the transformation to use
    Returns
    -------
    float
        Similarity value between the two melodies
    """
    # Validate inputs
    validate_method(method)
    validate_transformation(transformation)

    # Convert arrays to comma-separated strings (works with both lists and numpy arrays)
    pitches1_str = ",".join(map(str, melody1_pitches))
    starts1_str = ",".join(map(str, melody1_starts))
    ends1_str = ",".join(map(str, melody1_ends))
    pitches2_str = ",".join(map(str, melody2_pitches))
    starts2_str = ",".join(map(str, melody2_starts))
    ends2_str = ",".join(map(str, melody2_ends))

    # Create R script for similarity calculation
    r_script = f"""
    suppressMessages(suppressWarnings({{
        library(melsim)
        # Create melody objects
        melody1 <- melody_factory$new(mel_data = tibble::tibble(
            onset = c({starts1_str}),
            pitch = c({pitches1_str}),
            duration = c({ends1_str}) - c({starts1_str})
        ))
        melody2 <- melody_factory$new(mel_data = tibble::tibble(
            onset = c({starts2_str}),
            pitch = c({pitches2_str}),
            duration = c({ends2_str}) - c({starts2_str})
        ))
        # Create similarity measure
        sim_measure <- sim_measure_factory$new(
            name = "{method}",
            full_name = "{method}",
            transformation = "{transformation}",
            parameters = list(),
            sim_measure = "{method}"
        )
        # Calculate similarity
        result <- melody1$similarity(melody2, sim_measure)
        cat(jsonlite::toJSON(result$sim))
    }}))
    """

    # Run R script
    try:
        result = subprocess.run(
            ["Rscript", "-e", r_script], capture_output=True, text=True, check=True
        )
        # Extract JSON from output (may contain warnings before the JSON)
        output_str = result.stdout.strip()
        # Find the JSON part - look for the last line or the part after newline
        lines = output_str.split("\n")
        json_str = lines[-1]  # JSON should be on the last line

        # If that doesn't work, try to find JSON array/object markers
        if not (
            json_str.startswith("[")
            or json_str.startswith("{")
            or json_str.startswith('"')
        ):
            for line in reversed(lines):
                if line.startswith("[") or line.startswith("{") or line.startswith('"'):
                    json_str = line
                    break

        output = json.loads(json_str)

        # Handle both single values and lists
        if isinstance(output, list):
            value = output[0]  # Get first value if it's a list
        else:
            value = output

        # Handle NA values from R
        if value == "NA" or value is None:
            return float("nan")  # Return NaN for invalid combinations

        return float(value)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error calculating similarity: {e.stderr}")


def _convert_strings_to_tuples(d: Dict) -> Dict:
    """Convert string keys back to tuples where needed."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _convert_strings_to_tuples(v)
        else:
            result[k] = v
    return result


def score_to_arrays(score) -> Tuple[List[int], List[float], List[float]]:
    """Extract melody attributes from a Score object.
    Parameters
    ----------
    score : Score
        Score object containing a monophonic melody
    Returns
    -------
    Tuple[List[int], List[float], List[float]]
        Tuple of (pitches, start_times, end_times)
    """
    from amads.core.basics import Note
    from amads.pitch.ismonophonic import ismonophonic

    assert ismonophonic(score), "Score must be monophonic"

    # Flatten the score to get notes in order
    flattened_score = score.flatten(collapse=True)
    notes = list(flattened_score.find_all(Note))

    # Extract onset, pitch, duration for each note
    pitches = [note.pitch.key_num for note in notes]
    starts = [note.onset for note in notes]
    ends = [note.onset + note.duration for note in notes]

    return pitches, starts, ends


def _batch_compute_similarities(args_list: List[Tuple]) -> List[float]:
    """Compute similarities for a batch of melody pairs.
    Parameters
    ----------
    args_list : List[Tuple]
        List of argument tuples for _compute_similarity
    Returns
    -------
    List[float]
        List of similarity values
    """
    # Create R script for batch similarity calculation with improved efficiency
    r_script = """
    suppressMessages(suppressWarnings({
        library(melsim)
        library(jsonlite)
        library(purrr)
    # Function to create melody object
    create_melody <- function(pitches, starts, ends) {
        melody_factory$new(mel_data = tibble::tibble(
            onset = as.numeric(strsplit(starts, ",")[[1]]),
            pitch = as.numeric(strsplit(pitches, ",")[[1]]),
            duration = as.numeric(strsplit(ends, ",")[[1]]) - as.numeric(strsplit(starts, ",")[[1]])
        ))
    }
    # Function to calculate similarity
    calc_similarity <- function(melody1, melody2, method, transformation) {
        sim_measure <- sim_measure_factory$new(
            name = method,
            full_name = method,
            transformation = transformation,
            parameters = list(),
            sim_measure = method
        )
        result <- melody1$similarity(melody2, sim_measure)
        result$sim
    }
    # Process command line arguments
    args <- commandArgs(trailingOnly = TRUE)
    n_args <- length(args)
    n_comparisons <- n_args / 8  # Each comparison has 8 arguments
    # Pre-allocate results vector
    results <- numeric(n_comparisons)
    # Create a cache for melody objects
    melody_cache <- new.env()
    # Process in chunks for better memory management
    chunk_size <- 1000
    n_chunks <- ceiling(n_comparisons / chunk_size)
    for (chunk in seq_len(n_chunks)) {
        start_idx <- (chunk - 1) * chunk_size + 1
        end_idx <- min(chunk * chunk_size, n_comparisons)
        # Process chunk
        for (i in start_idx:end_idx) {
            idx <- (i-1) * 8 + 1
            # Get or create melody1
            melody1_key <- paste(args[idx], args[idx+1], args[idx+2], sep="|")
            if (!exists(melody1_key, envir=melody_cache)) {
                melody_cache[[melody1_key]] <- create_melody(args[idx], args[idx+1], args[idx+2])
            }
            melody1 <- melody_cache[[melody1_key]]
            # Get or create melody2
            melody2_key <- paste(args[idx+3], args[idx+4], args[idx+5], sep="|")
            if (!exists(melody2_key, envir=melody_cache)) {
                melody_cache[[melody2_key]] <- create_melody(args[idx+3], args[idx+4], args[idx+5])
            }
            melody2 <- melody_cache[[melody2_key]]
            method <- args[idx+6]
            transformation <- args[idx+7]
            results[i] <- calc_similarity(melody1, melody2, method, transformation)
        }
        # Force garbage collection after each chunk
        gc()
    }
    cat(toJSON(results))
    }))
    """

    # Prepare all arguments
    all_args = []
    for melody1_data, melody2_data, method, transformation in args_list:
        # Convert lists to comma-separated strings
        pitches1_str = ",".join(map(str, melody1_data[0]))
        starts1_str = ",".join(map(str, melody1_data[1]))
        ends1_str = ",".join(map(str, melody1_data[2]))
        pitches2_str = ",".join(map(str, melody2_data[0]))
        starts2_str = ",".join(map(str, melody2_data[1]))
        ends2_str = ",".join(map(str, melody2_data[2]))

        all_args.extend(
            [
                pitches1_str,
                starts1_str,
                ends1_str,
                pitches2_str,
                starts2_str,
                ends2_str,
                method,
                transformation,
            ]
        )

    # Run R script with all arguments
    try:
        result = subprocess.run(
            ["Rscript", "-e", r_script] + all_args,
            capture_output=True,
            text=True,
            check=True,
        )
        # Extract JSON from output (may contain warnings before the JSON)
        output_str = result.stdout.strip()
        # Find the JSON part - look for the last line or the part after newline
        lines = output_str.split("\n")
        json_str = lines[-1]  # JSON should be on the last line

        # If that doesn't work, try to find JSON array/object markers
        if not (
            json_str.startswith("[")
            or json_str.startswith("{")
            or json_str.startswith('"')
        ):
            for line in reversed(lines):
                if line.startswith("[") or line.startswith("{") or line.startswith('"'):
                    json_str = line
                    break

        parsed_result = json.loads(json_str)
        # Handle NA values from R
        return [
            float("nan") if x == "NA" or x is None else float(x) for x in parsed_result
        ]
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error calculating similarities: {e.stderr}")


def get_similarities(
    scores: Dict[str, object],
    method: Union[str, List[str]] = "Jaccard",
    transformation: Union[str, List[str]] = "pitch",
    output_file: Union[str, Path] = None,
    n_cores: int = None,
    batch_size: int = 1000,
) -> Union[
    Dict[str, Dict[str, float]], Dict[Tuple[str, str], Dict[str, Dict[str, float]]]
]:
    """Calculate pairwise similarities between multiple Score objects.

    You can provide a single method and transformation, or a list of methods and transformations.
    The function will return similarity matrices as nested dictionaries.

    Parameters
    ----------
    scores : Dict[str, Score]
        Dictionary mapping score names to Score objects
    method : Union[str, List[str]], default="Jaccard"
        Name of the similarity method(s) to use. Can be a single method or a list of methods.
    transformation : Union[str, List[str]], default="pitch"
        Name of the transformation(s) to use. Can be a single transformation or a list of transformations.
    output_file : Union[str, Path], optional
        If provided, save results to this file. If no extension is provided, .json will be added.
    n_cores : int, optional
        Number of CPU cores to use for parallel processing. Defaults to all available cores.
    batch_size : int, default=1000
        Number of comparisons to process in each batch

    Returns
    -------
    Union[Dict[str, Dict[str, float]], Dict[Tuple[str, str], Dict[str, Dict[str, float]]]]
        If single method and transformation: nested dictionary similarity matrix {row_name: {col_name: similarity}}
        If multiple methods/transformations: dictionary mapping (method, transformation) tuples to similarity matrices
    """
    # Convert single method/transformation to lists
    methods = [method] if isinstance(method, str) else method
    transformations = (
        [transformation] if isinstance(transformation, str) else transformation
    )

    # Validate all methods and transformations
    for m in methods:
        validate_method(m)
    for t in transformations:
        validate_transformation(t)

    if len(scores) < 2:
        raise ValueError("Need at least 2 Score objects for comparison")

    # Extract melody data from all scores (avoid multiprocessing due to Score object pickling issues)
    print("Extracting melody data...")
    melody_data = {}
    for name, score in tqdm(scores.items(), desc="Processing Score objects"):
        try:
            melody_data[name] = score_to_arrays(score)
        except Exception as e:
            print(f"Warning: Could not extract melody data for {name}: {str(e)}")

    if len(melody_data) < 2:
        raise ValueError("Need at least 2 valid Score objects for comparison")

    # Prepare arguments for parallel processing
    print("Computing similarities...")
    args = []
    score_pairs = []

    # Pre-compute all combinations for better performance
    combinations_list = list(combinations(melody_data.items(), 2))
    for (name1, data1), (name2, data2) in combinations_list:
        for m in methods:
            for t in transformations:
                args.append((data1, data2, m, t))
                score_pairs.append((name1, name2, m, t))

    # Process in larger batches for better performance
    similarities_list = []
    for i in tqdm(range(0, len(args), batch_size), desc="Processing batches"):
        batch = args[i : i + batch_size]
        similarities_list.extend(_batch_compute_similarities(batch))

    # Create dictionary of results
    similarities = dict(zip(score_pairs, similarities_list))

    # Convert to matrix format using native Python types
    score_names = list(scores.keys())

    # Create similarity matrices as nested dictionaries
    matrices = {}

    for m in methods:
        for t in transformations:
            # Initialize matrix as nested dictionary with 1s on diagonal
            sim_matrix = {}
            for name1 in score_names:
                sim_matrix[name1] = {}
                for name2 in score_names:
                    if name1 == name2:
                        sim_matrix[name1][name2] = 1.0
                    else:
                        sim_matrix[name1][name2] = 0.0

            # Fill matrix with pairwise similarities
            # Since combinations() only gives us each pair once, set both directions
            for (
                name1,
                name2,
                method_key,
                transformation_key,
            ), similarity in similarities.items():
                if method_key == m and transformation_key == t:
                    # Handle NaN values consistently
                    if (
                        similarity == "NA"
                        or similarity is None
                        or (isinstance(similarity, float) and math.isnan(similarity))
                    ):
                        sim_value = float("nan")
                    else:
                        sim_value = float(similarity)

                    # Set both directions to ensure perfect symmetry
                    sim_matrix[name1][name2] = sim_value
                    sim_matrix[name2][name1] = sim_value

            matrices[(m, t)] = sim_matrix

    # Save to file if output file specified
    if output_file:
        print("Saving results...")

        # Ensure output file has .json extension
        output_file = Path(output_file)
        if not output_file.suffix:
            output_file = output_file.with_suffix(".json")

        # Save matrices to JSON
        output_data = {}
        for (m, t), matrix in matrices.items():
            output_data[f"{m}_{t}"] = matrix

        import json

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Results saved to {output_file}")

    # Return format depends on number of method/transformation combinations
    if len(methods) == 1 and len(transformations) == 1:
        # Single method and transformation: return just the matrix
        return matrices[(methods[0], transformations[0])]
    else:
        # Multiple methods/transformations: return dictionary of matrices
        return matrices
