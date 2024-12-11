Documentation
=============

This guide explains how to build and maintain the project's documentation using Sphinx.

Prerequisites
-------------

Before building the documentation, ensure you have the dev dependencies installed:

.. code-block:: bash

    pip install -e ".[dev]"

Building documentation
----------------------

macOS or Linux
~~~~~~~~~~~~~~

.. code-block:: bash

    cd docs
    make preview

This will start a live server that automatically rebuilds the documentation when changes are detected.

By default only changed files are rebuilt. To clean the build directory, so that subsequent builds are made from scratch, run:

.. code-block:: bash

    make clean

Windows
~~~~~~~

.. code-block:: bash

    cd docs
    make.bat html

This will build the documentation once, you will then have to open it from the file path ``docs/_build/html/index.html``.

As above, you can clean the build directory so that subsequent builds are made from scratch:

.. code-block:: bash

    make.bat clean


Writing documentation
---------------------

Documentation files are written in reStructuredText (RST) format. Here are some key points:

- Use ``.rst`` extension for documentation files
- Follow the numpydoc style for docstrings
- Include code examples using ``.. code-block:: python`` blocks
- Cross-reference other pages using ``:ref:`` roles
- Add new pages to the appropriate toctree in ``index.rst``

For example:

.. code-block:: rst

    .. code-block:: python

        def example_function():
            """
            This is a docstring example.

            Parameters
            ----------
            None

            Returns
            -------
            None
            """
            pass

You can also write markdown files, which will be rendered using the ``myst_parser`` extension.

Adding new documentation files
------------------------------

To add a new documentation file:

1. Create a new ``.rst`` file in the appropriate directory:

   .. code-block:: bash

       touch docs/user_guide/new_feature.rst

2. Add content to your RST file using reStructuredText syntax:

   .. code-block:: rst

       New feature guide
       =================

       This is a guide for the new feature.

       Section title
       -------------

       Content goes here.

3. Add the file to the toctree in ``index.rst`` or another parent document:

   .. code-block:: rst

       .. toctree::
          :maxdepth: 2
          :caption: Contents:

          user_guide/existing_page
          user_guide/new_feature   # Add your new file here

The file will now appear in the documentation navigation. Make sure to:

- Use descriptive filenames that reflect the content
- Place files in appropriate subdirectories (user_guide, developer_notes, etc.)
- Keep the toctree organized and logical
- Build and check that the new page appears correctly


Troubleshooting
---------------

Common issues and solutions:

1. **Missing modules**: If you see warnings about missing modules, ensure all development
   dependencies are installed:

   .. code-block:: bash

       pip install -e .[docs]

2. **Build errors**: Clear the build directory and rebuild:

   .. code-block:: bash

       rm -rf docs/_build/*  # Unix/macOS
       # or
       rmdir /s /q docs\_build  # Windows
       make html
