# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "amads"
copyright = "2024, The AMADS team"
author = "The AMADS team"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_gallery.gen_gallery",
    "myst_parser",
]

# Configure napoleon for numpy style
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

# Configure autodoc and typehints
autodoc_typehints = "description"
always_document_param_types = True
typehints_use_signature_return = True
typehints_fully_qualified = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Configure sphinx-gallery
sphinx_gallery_conf = {
    "examples_dirs": "../examples",  # input directory
    "gallery_dirs": "auto_examples",  # output directory
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
