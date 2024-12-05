Style
=====

Code style
----------

This document outlines the coding style guidelines for contributing to this project.

Author attribution
~~~~~~~~~~~~~~~~

Author attribution should be included at the top of each module using ``__author__``. Use only names, no email addresses::

    __author__ = "Huw Cheston"

For multiple authors, use a list::

    __author__ = ["Huw Cheston", "Mark Gotham"]

Code organization
~~~~~~~~~~~~~~~~

Modules should be organized in a logical hierarchy that reflects their purpose. For example, complexity algorithms go in::

    algorithm/complexity/lz77.py

Note that functions will be importable in multiple ways::

    from musmart.algorithm.complexity.lz77 import lz77_size
    from musmart import lz77_size

Function naming
~~~~~~~~~~~~~~

Be explicit about what functions return. Don't make users guess::

    # Good
    lz77_size()
    lz77_compression_ratio()

    # Bad 
    lz77()  # Unclear what this returns

Code structure
~~~~~~~~~~~~~

Local function definitions should be avoided as they can negatively impact performance. Instead, define functions at module level::

    # Good
    def helper_function(x):
        return x * 2

    def main_function(x):
        return helper_function(x)

    # Bad
    def main_function(x):
        def helper_function(x):  # Defined locally - avoid this
            return x * 2
        return helper_function(x)

We plan to implement a pipeline for standardizing code formatting using ``black``. This will ensure consistent code style across the project.

Docstrings should use numpydoc formatting with type hints in the source code::

    def calculate_entropy(pitches: list[int]) -> float:
        """Calculate the entropy of a pitch sequence.
        
        Parameters
        ----------
        pitches
            List of MIDI pitch numbers
            
        Returns
        -------
        float
            Entropy value between 0 and 1
            
        Examples
        --------
        >>> calculate_entropy([60, 62, 64])
        0.682
        """
        pass

External package imports (except numpy) should be done locally within functions for efficiency. This avoids loading unused dependencies::

    # Good
    def plot_histogram(data):
        import matplotlib.pyplot as plt  # Import inside function
        plt.hist(data)
        plt.show()

    # Bad
    import matplotlib.pyplot as plt  # Global import - avoid this
    
    def plot_histogram(data):
        plt.hist(data)
        plt.show()

Types
~~~~~

- Functions should accept Python base types as inputs but can optionally support numpy arrays
- Return Python base types by default, use numpy types only when necessary
- For internal computations, either base Python or numpy is fine
- Where possible, only take simple singular input types and let users handle iteration

Common patterns
~~~~~~~~~~~~~~

Internal vs external functions:

- Internal functions often implement the core algorithm or equation from a paper
- External functions handle type checking, validation, and conversion

For example::

    def _calculate_entropy_core(counts: list[int]) -> float:
        """Core entropy calculation from Shannon (1948).
        
        Internal function that implements the entropy formula.
        Assumes input has been validated.
        """
        total = sum(counts)
        probabilities = [c/total for c in counts]
        return -sum(p * math.log2(p) for p in probabilities if p > 0)

    def calculate_entropy(pitches: list[int]) -> float:
        """Calculate the entropy of a pitch sequence.
        
        Handles input validation and conversion before calling _calculate_entropy_core().
        """
        if not pitches:
            raise ValueError("Input pitch list cannot be empty")
            
        # Convert pitches to counts
        from collections import Counter
        counts = list(Counter(pitches).values())
        
        return _calculate_entropy_core(counts)

References
~~~~~~~~~~

Include references with DOIs/URLs where possible. Here are some examples::

    [1]: Ziv, J., & Lempel, A. (1977). A universal algorithm for sequential data compression. 
         IEEE Transactions on Information Theory. 23/3 (pp. 337–343).
         https://doi.org/10.1109/TIT.1977.1055714

    [2]: Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024). 
         Rhythmic qualities of jazz improvisation predict performer identity and style 
         in source-separated audio recordings. Royal Society Open Science. 11/11.
         https://doi.org/10.1098/rsos.231023
