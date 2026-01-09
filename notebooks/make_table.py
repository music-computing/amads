"""
Basic script to make a README with a table for the notebooks in this dir.

Includes a test that the listings here match those in the dir (by file name).
"""

preamble = [
    "# Coding Notebooks for AMADS (Algorithms for Music Analysis and Data Science)",
    "These notebooks serve to demonstrate topics in the repo and associated book.",
    "If you have any questions or comments, "
    "please raise an issue, submit a pull request or otherwise get in touch with the maintainers: "
    "[Mark Gotham](https://markgotham.github.io/) and Roger Dannenberg."
]


items = [  # NB: use caps and underscore. (Title, difficulty, notes) tuples.
    ("Install", 1, "Simple demonstration of installation options, both via pip package (recommended) and locally."),
    ("Explore_Sound", 1, "Simple demonstration of audio data and sounds as distinct from symbolic data."),
    ("Explore_Symbolic", 1, "Simple demonstration of symbolic data and basics of how to access it with AMADS."),
    ("nPVI_fugue", 4, "Implement nPVI from scratch and apply to score/s.")
]


colab_part = "[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
git_base_part = "(https://colab.research.google.com/github/music-computing/amads/blob/main/"


def test_match() -> None:
    from pathlib import Path
    files = [str(x) for x in Path(".").glob("*.ipynb")]
    files.sort()
    names = [x[0].lower() + ".ipynb" for x in items]
    names.sort()
    assert files == names


if __name__ == "__main__":

    test_match()

    with open("README.md", "w") as text_file:
        [text_file.write(x + "\n\n") for x in preamble]
        heads = ("Topic", "Local Notebook", "Colab", "Difficulty", "Notes")
        text_file.write('| ' + ' | '.join(heads) + ' |\n')
        text_file.write('| ' + ' | '.join(["---"] * len(heads)) + ' |\n')
        for x in items:
            text_file.write(
                '| ' + ' | '.join(
                    [
                        f'{x[0].replace("_", " ")}',
                        f'[Notebook]({x[0].lower()}.ipynb)',
                        colab_part + git_base_part + x[0].lower() + '.ipynb)',
                        str(x[1]),  # difficulty
                        x[2]  # notes
                    ]
                ) + ' |\n'
            )
