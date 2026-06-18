# Demo Configurations

This folder contains sample configurations for `interactive.yaml`.

- `interactive_demo.yaml` – A minimal example following our psychological risk scale format. You can copy this file as your starting `interactive.yaml` when experimenting with AnnaAgent.
- `family_stress_case.json` – A family-stress case with `id`, `conversation`, `report`, and `portrait` fields. The `conversation` field is the previous-session conversation history used as long-term memory.

You can index a sample into LanceDB long-term memory with:

```bash
uv run anna-agent memory index docs/family_stress_case.json
```
