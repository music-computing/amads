# Algorithms for Music Analysis and Data Science (AMADS)

[![codecov](https://codecov.io/gh/music-computing/amads/graph/badge.svg?token=TONE1IFOR3)](https://codecov.io/gh/music-computing/amads)
[![Tests](https://github.com/music-computing/amads/actions/workflows/tests.yml/badge.svg)](https://github.com/music-computing/amads/actions/workflows/tests.yml)
[![Docs](https://github.com/music-computing/amads/actions/workflows/documentation.yml/badge.svg)](https://github.com/music-computing/amads/actions/workflows/documentation.yml)

This repository represents the very earliest stages of an attempt to collect and organise algorithms for
music analysis and data science.
If you are interested in participating, please get in touch with one of
Peter Harrison (pmch2@cam.ac.uk), Mark Gotham (`<first_name>dot<last_name>@kcl.ac.uk`), or Roger Dannenberg.

Much functionality in this package still remains to be tested/implemented/documented.
Use at your own risk!

For more on the ...
- ... package in general, see the [documentation website](https://music-computing.github.io/amads)
- ... motivation and background, please see [the draft paper](./paper.md)

## Installation

To use AMADS we recommend cloning the repository and installing it in editable mode. So:

```py
cd ~/Documents  # or wherever you want to put the package
git clone https://github.com/music-computing/amads.git
pip install -e amads
```

## Design principles

1. We opt to create one repository, in one langauge, rather than attempting to list / direct to others.
   - It makes sense to have a single reference language for interoperability, comparison and more.
   - The sources are far-flung, in many code languages, and not interoperable.
2. The language is Python, for all the usual reasons, chief among them being it popularity.
   - some designers of computer languages programming languages may find that a rather shallow reason,
   - but commitment to access and interoperability makes a language"s existing popularity critically important.
   - e.g., we have in mind the student of music who gets that computing will open things up for them, but who also wants the time they invest in learning the ropes to be transferable in case they ever want or need to move away from music computing (imagine!).
3. Algorithms are linked to a credible publication
   - ... or other demonstrable take-up by the community.
   - implemented here as exactly as reference to the source allows (usually from scratch)
   - Open source, well documented, etc.

## Uses

We welcome all and any use cases.
Among them, those we have had in mind during the development include:
- researchers using existing algorithms "off the shelf" for specific tasks, including comparison with a new approach
- students learning a standard algorithm by implementing is from scratch and comparing the output with a reference implementation.
- those considering entry into the field to browse all this casually.


## Contributions

... are welcome!

Please pitch in relevant material, making sure to include any relevant citation.
Equally, please feel free to add issues for algorithms you'd like to see us implement and include here.

