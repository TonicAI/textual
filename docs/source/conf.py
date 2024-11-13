# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import mock

MOCK_MODULES = ["numpy", "pandas", "tqdm", "tqdm.utils", "amplitude"]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------

project = "Tonic Textual"
copyright = "2024, Tonic AI"
author = "Adam Kamor, Ander Steele, Joe Ferrara, Ethan Philpott, Lyon Van Voorhis, Kirill Medvedev, Travis Matthews"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.googleanalytics",
]
autosummary_generate = True
source_suffix = [".rst"]

# Napoleon settings
napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True
napoleon_include_init_with_doc = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

html_theme = "sphinx_rtd_theme"


html_favicon = "./_static/tonic-textual-logo.svg"
html_logo = "./_static/textual-logo.png"
html_show_sourcelink = False
html_show_sphinx = False
html_theme_options = {
    "analytics_anonymize_ip": False,
    "logo_only": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "white",
    "flyout_display": "hidden",
    "version_selector": False,
    "language_selector": True,
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

extensions += []

html_title = "Tonic Textual Python SDK Documentation"

pygments_style = "sphinx"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["custom.css"]
# html_permalinks_icon = Icons.permalinks_icon

# function signature
python_maximum_signature_line_length = 20
python_display_short_literal_types = True

# google analytics
googleanalytics_id = "G-F8WSWZQ7PC"
googleanalytics_enabled = True
