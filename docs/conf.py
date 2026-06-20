import os
from pathlib import Path

project = "AnnaAgent"
author = "AnnaAgent contributors"
copyright = "2026, AnnaAgent contributors"
release = "0.3.1"
version = "0.3.1"
docs_language = os.environ.get("ANNA_DOCS_LANGUAGE", "en")

extensions = [
    "sphinx_copybutton",
]

templates_path = [str(Path(__file__).parent / "_templates")]
root_doc = "index"
source_suffix = {
    ".rst": "restructuredtext",
}

html_theme = "furo"
html_title = (
    "AnnaAgent 文档" if docs_language.startswith("zh") else "AnnaAgent Documentation"
)
html_baseurl = (
    "https://sci-m-wang.github.io/AnnaAgent/zh/"
    if docs_language.startswith("zh")
    else "https://sci-m-wang.github.io/AnnaAgent/"
)
html_static_path = [str(Path(__file__).parent / "_static")]
html_css_files = ["custom.css"]
html_js_files = ["language-switch.js"]
html_theme_options = {
    "source_repository": "https://github.com/sci-m-wang/AnnaAgent/",
    "source_branch": "main",
    "source_directory": "docs/en/",
}

language = "zh_CN" if docs_language.startswith("zh") else "en"
locale_dirs = [str(Path(__file__).parent / "locale")]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

nitpicky = False
suppress_warnings = ["misc.highlighting_failure"]

_static = Path(__file__).parent / "_static"
_static.mkdir(exist_ok=True)
