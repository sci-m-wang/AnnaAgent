from pathlib import Path

project = "AnnaAgent"
author = "AnnaAgent contributors"
copyright = "2026, AnnaAgent contributors"
release = "0.2.0"
version = "0.2.0"

extensions = [
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "README.md", "Thumbs.db", ".DS_Store"]
root_doc = "index"
source_suffix = {
    ".rst": "restructuredtext",
}

html_theme = "furo"
html_title = "AnnaAgent Documentation"
html_baseurl = "https://sci-m-wang.github.io/AnnaAgent/"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "source_repository": "https://github.com/sci-m-wang/AnnaAgent/",
    "source_branch": "main",
    "source_directory": "docs/",
}

language = "en"
locale_dirs = []

nitpicky = False
suppress_warnings = ["misc.highlighting_failure"]

_static = Path(__file__).parent / "_static"
_static.mkdir(exist_ok=True)
