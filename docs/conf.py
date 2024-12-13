# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from pathlib import Path
from importlib.metadata import version as _version
import sys
from unittest.mock import Mock

# Mock _ok module
sys.modules["_ok"] = Mock()

project = "miniscope-io"
copyright = "2023, Jonny"
author = "Jonny, Takuya"
release = _version("mio")
html_title = "mio"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.graphviz",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_click",
    "sphinx_design",
    "sphinxcontrib.autodoc_pydantic",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.programoutput",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "rich": ("https://rich.readthedocs.io/en/stable/", None),
    "pyserial": ("https://pyserial.readthedocs.io/en/stable/", None),
}

# ----------
# package settings
# ----------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# graphviz
graphviz_output_format = "svg"


# autodoc
# Mock imports for packages we don't have yet - this one is
# for opal kelley stuff we need to figure out the licensing for
autodoc_mock_imports = ["routine"]

# todo
todo_include_todos = True

# mermaid

mermaid_include_elk = "latest"
mermaid_version = None
mermaid_use_local = "https://example.com"
mermaid_init_js = """
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.esm.min.mjs'
import elkLayouts from 'https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk/dist/mermaid-layout-elk.esm.min.mjs';
mermaid.registerLayoutLoaders(elkLayouts);
const make_config = () => {
  let prefersDark = localStorage.getItem('theme') === 'dark' || (localStorage.getItem('theme') === null && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
  return({
    startOnLoad:false,
    darkMode: prefersDark,
    theme: prefersDark ? "dark" : "default"
  })
}

const init_mermaid = () => {
    let graphs = document.querySelectorAll(".mermaid");
    [...graphs].forEach((element) => {
        if (!element.hasAttribute("data-source")) {
            element.setAttribute("data-source", element.innerText);
        }
        if (element.hasAttribute("data-processed")) {
            let new_elt = document.createElement("pre");
            let graph_source = element.getAttribute("data-source");
            new_elt.appendChild(document.createTextNode(graph_source));
            new_elt.classList.add("mermaid");
            new_elt.setAttribute("data-source", graph_source);
            element.replaceWith(new_elt);
        }
    });

    let config = make_config()
    mermaid.initialize(config);
    mermaid.run();
}

init_mermaid();

let theme_observer = new MutationObserver(init_mermaid);
let body = document.getElementsByTagName("body")[0];
theme_observer.observe(body, {attributes: true});
window.theme_observer = theme_observer;

"""

# inheritance graphs
inheritance_graph_attrs = {
    "rankdir": "TB",
}
