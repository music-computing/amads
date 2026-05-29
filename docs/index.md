<div style="display: flex; align-items: center; margin-bottom: 20px;">
  <img src="assets/logo-graphic.png" alt="AMADS Logo" style="width: 120px; margin-right: 15px; flex-shrink: 0;">
  <h1 style="margin: 0; line-height: 1.3;">Algorithms for Music Analysis and Data Science (AMADS)</h1>
</div>

This repository collects and organises algorithms for
music analysis and data science.
If you are interested in participating, please get in touch with
[Mark Gotham](https://markgotham.github.io/)
or [Roger Dannenberg](https://www.cs.cmu.edu/~rbd).

Much functionality in this package still remains to be tested/implemented/documented.
Use at your own risk!

- For package functions, see the [API Reference](./core.md)
- For motivation and background, please see [the draft paper](paper.md)
- For information for developers, see [Developer Notes](developer_notes/documentation.md)
- For installation, see below and [Installation](user_guide/installation.md)

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
    - That said, we do use AMADS as a kind of meta-package to connect
   to external well-maintained libraries (including those not in
   Python) when this makes the implementation substantially easier.
2. The language is Python, for all the usual reasons, chief among them
   being its popularity.
    - some experienced programmers may find that a rather shallow reason,
    - but commitment to access and interoperability makes a language's existing popularity critically important.
    - E.g., we have in mind the student of music who gets that computing will open things up for them, but who also wants the time they invest in learning the ropes to be transferable in case they ever want or need to move away from music computing (imagine!).
3. Algorithms are:
    - linked to a credible publication or other demonstrable take-up by the community,
    - implemented here as exactly as reference to the source allows (usually from scratch), or with clear commentary on any changes,
    - open-source, 
    - well documented.

## Uses

We welcome all and any use cases.
Among them, those we have had in mind during the development include:

- researchers using existing algorithms “off the shelf” for specific tasks, including comparison with a new approach,
- students learning a standard algorithm by implementing it from scratch and comparing the output with a reference implementation,
- those considering entry into the field to browse all this casually.


## Contributions

... are welcome!

Please pitch in relevant material, making sure to include any relevant citation.
Equally, please feel free to add issues (or write directly) to propose algorithms you'd like to see us implement and include here.
