# Demo Configurations

This folder contains sample configurations for `interactive.yaml`.

- `interactive_demo.yaml` – A minimal example following our psychological risk scale format. You can copy this file as your starting `interactive.yaml` when experimenting with AnnaAgent.
- `family_stress_case.json` – A family-stress case with `id`, `conversation`, `report`, and `portrait` fields. The `conversation` field is the previous-session conversation history used as long-term memory.

You can index a sample into LanceDB long-term memory with:

```bash
anna memory index docs/family_stress_case.json
```

## Sphinx documentation

The published GitHub Pages site uses Sphinx i18n/gettext. English source files
live under `docs/en`. Chinese translations live under
`docs/locale/zh_CN/LC_MESSAGES`.

```bash
rm -rf docs/_build/gettext docs/_build/html
uv run --group docs sphinx-build -W -b gettext -c docs docs/en docs/_build/gettext
uv run python docs/tools/check_i18n.py docs/_build/gettext docs/locale/zh_CN/LC_MESSAGES
ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
ANNA_DOCS_LANGUAGE=zh_CN uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html/zh
```

English is published at the site root. Chinese is published under `/zh/`, with a
language switcher linking corresponding pages.
