# Style

## Code style

This document outlines the coding style guidelines for contributing to
this project.

### Author attribution

Author attribution should be included at the top of each module using
`__author__`. Use only names, no email addresses:

    __author__ = "Huw Cheston"

For multiple authors, use a list:

    __author__ = ["Huw Cheston", "Mark Gotham"]

See [documentation][] for notes on getting your name into formatted
documentation (`__author__` will not do it).

### Code organization

Modules should be organized in a logical hierarchy that reflects their
purpose. For example, complexity algorithms go in:

    algorithm/complexity/lz77.py

Note that functions will be importable in multiple ways:

    from amads.harmony.root_finding.parncutt_1988 import root
    from amads.all import root_parncutt_1988

The first style is more verbose, but it makes the logical organization
of the package more explicit. The second style is more appropriate for
interactive use.

In order to support the second style, we add import statements to the
`amads/all.py` file for *everything*.

Then the `__init__.py` file for nearly all directories is empty.

#### Details on module organization and naming

We initially set up `__init__.py` files to include everything beneath
them. This might be nice so that you could simply write

    from amads.harmony import get_root

skipping the detail that `get_root` might actually be in a
submodule `amads.harmony.root_finding` or
`amads.harmony.root_finding.parncutt` but this "aggressive" loading
is:

 - well, aggressive, loading much more than necessary
 - caused some cyclical dependencies
 - does not match mkdocs documentation, which would describe
    `get_root` as `amads.harmony.root_finding.parncutt.get_root`,
    not `amads.harmony.get_root`

In short, attempts to create “virtual” namespaces that do not match
the directory structure conflict in subtle ways with Python tools.
In spite of Python's popularity and goals of simplicity, I think there
is obvious confusion and design failure in Python abstractions. In
the end, it seems “simpler is better,” and trying to create “helpful”
abstractions (like a harmony module with all things harmony) just
adds to confusion and maintenance problems.

### Function naming

Be explicit about what functions return. Don't make users guess:

    # Good
    lz77_size()
    lz77_compression_ratio()

    # Bad
    lz77()  # Unclear what this returns

### Code structure

Local function definitions should be avoided as they can negatively
impact performance. Instead, define functions at module level:

    # Good
    def _helper_function(x):
        return x * 2

    def main_function(x):
        return _helper_function(x)

    # Bad
    def main_function(x):
        def helper_function(x):  # Defined locally - avoid this
            return x * 2
        return helper_function(x)

We implement a pipeline for standardizing code formatting using
`black`. This will ensure consistent code style across the project
at the expense of allowing “custom” formatting in special cases.
You can override `black` (e.g., this is done in `amads.core.basics`)
and “do it yourself” but please stick to the general Python
conventions seen throughout AMADS and avoid any surprising code
layout.

Docstrings should use numpydoc formatting:

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

External package imports (except numpy) should be done locally within
functions for efficiency. This avoids loading unused dependencies:

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

### Types

-   Provide type hints for function parameters and return types
-   If a function accepts either `float` or `int` you can use
    `float` as the type hint. `int` will be understood as being
    accepted too
-   Functions should accept Python base types as inputs but can
    optionally support numpy arrays.
-   Return Python base types by default, use numpy types only when
    necessary
-   For internal computations, either base Python or numpy is fine
-   Where possible, only take simple singular input types and let
    users handle iteration (well, we're not consistent on this point,
    so this policy may change. An argument for is simplifying type
    specifications, which in some cases are too complex to be really
    helpful.)

### Common patterns

When implementing algorithms, we distinguish between internal and
external functions. Internal functions implement the core algorithm or
equation. External functions wrap these internal implementations,
handling input validation, type checking, and any necessary data
conversion. This separation of concerns helps keep the core algorithmic
logic clean and focused while ensuring robust input handling at the API
level.

For example:

    # External function
    def calculate_entropy(pitches: list[int]) -> float:
        """Calculate the entropy of a pitch sequence.

        Handles input validation and conversion before
        calling _calculate_entropy_core().
        """
        if not pitches:
            raise ValueError("Input pitch list cannot be empty")

        # Convert pitches to counts
        from collections import Counter
        counts = list(Counter(pitches).values())

        return _calculate_entropy(counts)

    # Internal function
    def _calculate_entropy(counts: list[int]) -> float:
        """Core entropy calculation from Shannon (1948).

        Internal function that implements the entropy formula.
        Assumes input has been validated.
        """
        total = sum(counts)
        probabilities = [c/total for c in counts]
        return -sum(p * math.log2(p) for p in probabilities if p > 0)

Put the external function at the beginning of the module, so that it's
the first thing the user sees. Note that we prefix the internal function
with an underscore, to indicate that it's not part of the public API.

### Notes

In documentation, you can put the main points at the top and put
details in a collapsible box later on. We prefer to put Notes *after*
Attributes, Parameters, Returns, and Raises sections. If there is a
“note” that deserves to be seen more immediately, just write something
like:

    Note: see also [plot][amads.core.distribution.Distribution.plot]
    
while a full notes section would be written (below Parameters,
Returns, etc.):

    Notes
    -----
    
    - here is one detail we omitted in the docstring above
    - here is another detail
    - and the details just keep coming!


### References

Include references with DOIs/URLs where possible. Here are some
examples. Put References *below* Attributes, Parameters, Returns,
Raises and Notes sections.

    References
    ----------
    [1] Ziv, J., & Lempel, A. (1977). A universal algorithm for
         sequential data compression.
         IEEE Transactions on Information Theory. 23/3 (pp. 337–343).
         https://doi.org/10.1109/TIT.1977.1055714

    [2] Cheston, H., Schlichting, J. L., Cross, I., & Harrison, P. M. C. (2024).
         Rhythmic qualities of jazz improvisation predict performer
         identity and style in source-separated audio recordings.
         Royal Society Open Science. 11/11.
         https://doi.org/10.1098/rsos.231023
