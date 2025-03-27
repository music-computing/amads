from typing import Iterator, Optional


def float_range(start: float, end: Optional[float], step: float) -> Iterator[float]:
    """Generate a range of floats.

    Similar to Python's built-in range() function but supports floating point numbers.
    If end is None, generates an infinite sequence.

    Parameters
    ----------
    start : float
        The starting value of the range
    end : float or None
        The end value of the range (exclusive). If None, generates an infinite sequence
    step : float
        The increment between values

    Yields
    ------
    float
        The next value in the sequence
    """
    curr = start
    while end is None or curr < end:
        yield curr
        curr += step


def check_python_package_installed(package_name: str):
    """
    Check if a Python package is installed, raise error if not.

    Args:
        package_name: Name of the package to check

    Raises:
        ImportError: If package is not installed, with message suggesting pip install
    """
    try:
        __import__(package_name)
    except ImportError:
        raise ImportError(
            f"Package '{package_name}' is required but not installed. "
            f"Please install it using: pip install {package_name}"
        )
