# Documentation

This guide explains how to build and maintain the project\'s
documentation using Sphinx.

## Prerequisites

Before building the documentation, ensure you have the dev dependencies
installed:

```
pip3 install mkdocs mkdocs-material "mkdocstrings[python]"
in project root: mkdocs new .
```

## Building documentation

### macOS or Linux

```
PYTHONPATH=. mkdocs serve 
```

(You can write `build` instead of `serve` to just build once.)

This will start a live server that automatically rebuilds the
documentation when changes are detected. 

**However**, changes to Python source code will *not* rebuild.
I keep a small shell window running `PYTHONPATH=. mkdocs serve`.
After editing some docs in code, I go to the window and type
CTRL-C CTRL-P RETURN, which kills the server, recalls the
build command and runs it. When everything is updated, your
browser will update the page automatically.

### Windows

Can someone help with this?

## Writing documentation

Documentation files are written in MarkDown (.md) format. Here
are some key points:

-   Use `.md` extension for documentation files
-   Follow the numpydoc style for docstrings
-   Cross-reference other pages using `:ref:` roles
-   Add new pages to the appropriate toctree in `index.rst`

### Authorship

If you want to get credit in the formatted documentation, 
add something like this to a docstring: 

` <small>**Authors**: Yiming Huang, Roger B. Dannenberg</small>`

If the module appears in documentation, you can put this at
the bottom of the text of the module docstring (at the top of
the file).

In many cases, there is no special information associated with
the module, e.g., it is simply a container for algorithms. In
that case, we do not produce documentation for the module, and
you should put the author credit into the function(s) that *do*
appear in the documentation. Generally put the `**Authors**`
line *below* the descriptive strings for the function and *above*
the “`Parameters`” heading. See docs for `duration_distribution_1`
within Time : Distributions.


## Adding new documentation files

To add a new documentation file:

1.  Create a new `.md` file in the appropriate directory:

    ```
    touch docs/reference/melody/melody_info.md
    ```

2.  Add content to your .md file using MarkDown syntax:

```
# Extra Information on Melody Modules

This is a guide for users using functions in amads.melody

## Section title

Content goes here.
```

3.  Add the file to the nav: info near the bottom of
`mkdocs.yml` in the root of the repo.

```
nav:
  - Home: index.md
  - Project Overview: paper.md
  - API Reference:
    - Core:
      ...
    ...
    - Melody:
    ...
    - reference/melody/melody_info.md
    OR
    - AlternateTitle: reference/melody/melody_info.md
    ...
  ...
```

The file will now appear in the documentation navigation. Make sure to:

  - Use descriptive filenames that reflect the content
  -  Place files in appropriate subdirectories (reference,
      developer_notes, etc.)
  - Keep `mkdocs.yml` well-organized.
  - Build and check that the new page appears correctly

## Adding Code to Documentation

  - Note that modules are not directly added to `mkdocs.yml` in
      the root of the repo. Instead, you create a `.md` file
      (see previous section) that imports code documentation.
  - The relationship between modules and `.md` files is flexible
      since this is all manual: You can document multiple
      modules in a single page or even split a single module
      into multiple pages.
      
The syntax to “import” code documention into MarkDown is like
this:
```
::: amads.time.swing.match_beats_and_upbeats
```
The path can name an entire module, a class, or a function.

### Add the module?

If there is useful information in a doc-string at the top of
the module source code, then you should add the module to
`mkdocs.yml`. However, *this will (by default) add all the*
content *of the module as well* without *putting it in the
table-of-contents in the right margin!*

Therefore, if you add the module, you should disable
members like this:
```
::: amads.time.swing
    options:
      members: false
```
This example, in `docs/reference/time/swing.md`, adds general
documentation from the top of `amads/time/swing.py`, but it
does *not* add functions.

### Add classes and functions

Mkdocs does not automatically create documentation pages for
code, so for each topic, you need to create a .md file that
is included in `mkdocs.yml`. This example is from
`docs/reference/melody/swing.md`, which displays the documentation
for `amads/melody/swing.py`. Four functions (there are no classes)
are added to the page after the module documentation, which
naturally comes first:
```
::: amads.time.swing
    options:
      members: false

----------------

::: amads.time.swing.beat_upbeat_ratio 

------------------

::: amads.time.swing.mean_bur

------------------

::: amads.time.swing.std_bur

------------------

::: amads.time.swing.match_beats_and_upbeats
```
In this case the table of contents in the right margin
will have “swing”, “beat_upbeat_ratio”, “mean_bur”,
“std_bur” and “match_beats_and_upbeats”.

You can also add additional text to the `.md` page

This is referenced in `mkdocs.yml` like this:
```
nav:
  ...
  - API Reference:
    ...
    - Time
      ...
      - Swing: reference/time/swing.md
      ...
    ...
  ...
```
The page title, Swing, could also be put in the `swing.md` file.

## Troubleshooting

Common issues and solutions:

1.  **Missing modules**: If you see warnings about missing modules,
    ensure all development dependencies are installed:

    ``` bash
    pip install -e .[docs]
    ```

2.  **Build errors**: Clear the build directory and rebuild.

    ``` bash
    rm -rf docs/_build/*  # Unix/macOS
    # or
    rmdir /s /q docs\_build  # Windows
    make html
    ```
