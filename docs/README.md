# Demo Configurations

This folder contains sample configurations for `interactive.yaml`.

- `interactive_demo.yaml` – A minimal example following our psychological risk scale format. You can copy this file as your starting `interactive.yaml` when experimenting with AnnaAgent.
- `family_stress_case.json` – A family-stress case with `id`, `conversation`, `report`, and `portrait` fields. The `conversation` field is the previous-session conversation history used as long-term memory.

You can index a sample into LanceDB long-term memory with:

```bash
anna memory index docs/family_stress_case.json
```

## Sphinx documentation

The published GitHub Pages site is built as two separate Sphinx sites so readers
can switch languages instead of seeing both languages on one page:

```bash
ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
ANNA_DOCS_LANGUAGE=zh uv run --group docs sphinx-build -W -b html -c docs docs/zh docs/_build/html/zh
```

The English site is published at the root of GitHub Pages. The Chinese site is
published under `/zh/`.
