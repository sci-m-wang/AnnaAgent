from pathlib import Path

project = "AnnaAgent"
author = "AnnaAgent contributors"
copyright = "2026, AnnaAgent contributors"
release = "0.2.0"
version = "0.2.0"

extensions = [
    "sphinx_copybutton",
]

templates_path = [str(Path(__file__).parent / "_templates")]
root_doc = "index"
source_suffix = {
    ".rst": "restructuredtext",
}

html_theme = "furo"
html_title = "AnnaAgent Documentation"
html_baseurl = "https://sci-m-wang.github.io/AnnaAgent/"
html_static_path = [str(Path(__file__).parent / "_static")]
html_css_files = ["custom.css"]
html_js_files = ["language-switch.js"]
html_theme_options = {
    "source_repository": "https://github.com/sci-m-wang/AnnaAgent/",
    "source_branch": "main",
    "source_directory": "docs/",
}

language = "en"
locale_dirs = []
exclude_patterns = [
    "_build",
    "README.md",
    "Thumbs.db",
    ".DS_Store",
    "en/*",
    "zh/*",
]

nitpicky = False
suppress_warnings = ["misc.highlighting_failure"]

_static = Path(__file__).parent / "_static"
_static.mkdir(exist_ok=True)
