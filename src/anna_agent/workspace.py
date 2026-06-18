import json
from pathlib import Path
from typing import Any

import yaml

from .case_data import sample_case, write_case_json
from .config.init_content import INIT_DOTENV, INIT_INTERACTIVE_YAML, INIT_YAML

WORKSPACE_DIRS = ["assets", "cases", "prompts", "runs", "outputs", "logs", "cache"]


def default_asset_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "presets": {
            "paper": ["emotion-sft", "complaint-sft", "standard-data"],
        },
        "assets": [
            {
                "name": "emotion-sft",
                "kind": "model",
                "description": "SFT emotion model used by the paper experiments.",
                "target": "assets/models/emotion-sft",
                "source": {
                    "type": "huggingface",
                    "repo_id": "sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct",
                    "repo_type": "model",
                    "revision": "main",
                },
            },
            {
                "name": "complaint-sft",
                "kind": "model",
                "description": (
                    "SFT chief-complaint chain model used by the paper experiments."
                ),
                "target": "assets/models/complaint-sft",
                "source": {
                    "type": "huggingface",
                    "repo_id": "sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct",
                    "repo_type": "model",
                    "revision": "main",
                },
            },
            {
                "name": "standard-data",
                "kind": "dataset",
                "description": "Synthetic standard cases for reproducible experiments.",
                "target": "assets/data/standard",
                "source": {
                    "type": "huggingface",
                    "repo_id": "sci-m-wang/Anna-CPsyCounD",
                    "repo_type": "dataset",
                    "revision": "main",
                },
            },
        ],
    }


def initialize_workspace(path: Path, force: bool = False) -> None:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    for dirname in WORKSPACE_DIRS:
        directory = root / dirname
        directory.mkdir(exist_ok=True)
        keep = directory / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    _write_text(root / "settings.yaml", INIT_YAML, force)
    _write_text(root / "interactive.yaml", INIT_INTERACTIVE_YAML, force)
    _write_text(root / ".env.example", INIT_DOTENV, force)
    dotenv = root / ".env"
    if not dotenv.exists() or force:
        dotenv.write_text(INIT_DOTENV, encoding="utf-8")
    sample_path = root / "cases" / "family_stress_case.json"
    if force or not sample_path.exists():
        write_case_json(sample_case(), sample_path)
    _write_json(root / "assets" / "anna-assets.json", default_asset_manifest(), force)


def load_settings(workspace: Path) -> dict[str, Any]:
    path = workspace / "settings.yaml"
    if not path.exists():
        path = workspace / "settings.yml"
    if not path.exists():
        path = workspace / "settings.json"
    if not path.exists():
        raise FileNotFoundError(f"settings.yaml not found in {workspace}")
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_settings(workspace: Path, data: dict[str, Any]) -> None:
    path = workspace / "settings.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def set_config_value(workspace: Path, dotted_key: str, value: Any) -> None:
    data = load_settings(workspace)
    target = data
    keys = dotted_key.split(".")
    for key in keys[:-1]:
        child = target.get(key)
        if child is None:
            child = {}
            target[key] = child
        if not isinstance(child, dict):
            raise TypeError(f"Cannot set {dotted_key}: {key} is not a mapping")
        target = child
    target[keys[-1]] = value
    write_settings(workspace, data)


def update_env_values(workspace: Path, values: dict[str, str]) -> None:
    path = workspace / ".env"
    if not path.exists():
        path.write_text(INIT_DOTENV, encoding="utf-8")
    lines = path.read_text(encoding="utf-8").splitlines()
    remaining = {key: value for key, value in values.items() if value}
    updated: list[str] = []
    for line in lines:
        stripped = line.strip()
        candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
        if "=" not in candidate:
            updated.append(line)
            continue
        key = candidate.split("=", 1)[0].strip()
        if key in remaining:
            updated.append(f"{key}={_quote_env_value(remaining.pop(key))}")
        else:
            updated.append(line)
    if remaining:
        if updated and updated[-1]:
            updated.append("")
        updated.append("# Added by anna-agent config wizard")
        for key, value in remaining.items():
            updated.append(f"{key}={_quote_env_value(value)}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def redact_config(data: dict[str, Any]) -> dict[str, Any]:
    def redact(value: Any, key: str = "") -> Any:
        if isinstance(value, dict):
            return {
                item_key: redact(item_value, item_key)
                for item_key, item_value in value.items()
            }
        if any(
            token in key.lower() for token in ["key", "token", "secret", "password"]
        ):
            return "***" if value else value
        return value

    return redact(data)


def _write_text(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _quote_env_value(value: str) -> str:
    if not value or any(char.isspace() for char in value) or "#" in value:
        return json.dumps(value)
    return value
