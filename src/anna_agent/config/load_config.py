import json
import os
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import load_dotenv

from .models.anna_engine_config import AnnaEngineConfig

_default_config_files = ["settings.yaml", "settings.yml", "settings.json"]


def _search_for_config_in_root_dir(root: str | Path) -> Path | None:
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"Invalid config path: {root} is not a directory")
    for file in _default_config_files:
        if (root / file).is_file():
            return root / file
    return None


def _parse_env_variables(text: str) -> str:
    return Template(text).substitute(os.environ)


def _load_dotenv(config_path: Path | str) -> None:
    config_path = Path(config_path)
    dotenv_path = config_path.parent / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


def _get_config_path(root_dir: Path, config_filepath: Path | None) -> Path:
    if config_filepath:
        config_path = config_filepath.resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Specified Config file not found: {config_path}")
    else:
        config_path = _search_for_config_in_root_dir(root_dir)
    if not config_path:
        raise FileNotFoundError(f"Config file not found in root directory: {root_dir}")
    return config_path


def _apply_overrides(data: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        keys = key.split(".")
        target = data
        current_path = keys[0]
        for k in keys[:-1]:
            current_path += f".{k}"
            target_obj = target.get(k, {})
            if not isinstance(target_obj, dict):
                raise TypeError(
                    f"Cannot override non-dict value: data[{current_path}] is not a dict."
                )
            target[k] = target_obj
            target = target[k]
        target[keys[-1]] = value


def _parse(file_extension: str, contents: str) -> dict[str, Any]:
    if file_extension in {".yaml", ".yml"}:
        return yaml.safe_load(contents)
    if file_extension == ".json":
        return json.loads(contents)
    raise ValueError(
        f"Unable to parse config. Unsupported file extension: {file_extension}"
    )


def _flatten_config(data: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    model_service = data.get("model_service") or {}
    values["model_name"] = model_service.get("model_name")
    values["api_key"] = model_service.get("api_key")
    values["base_url"] = model_service.get("base_url")

    servers = data.get("servers") or {}
    complaint = servers.get("complaint") or {}
    values["complaint_api_key"] = complaint.get("api_key")
    values["complaint_base_url"] = complaint.get("base_url")

    counselor = servers.get("counselor") or {}
    values["counselor_api_key"] = counselor.get("api_key")
    values["counselor_base_url"] = counselor.get("base_url")

    emotion = servers.get("emotion") or {}
    values["emotion_api_key"] = emotion.get("api_key")
    values["emotion_base_url"] = emotion.get("base_url")
    return values


def load_config(
    root_dir: Path,
    config_filepath: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AnnaEngineConfig:
    root = root_dir.resolve()
    config_path = _get_config_path(root, config_filepath)
    _load_dotenv(config_path)
    config_extension = config_path.suffix
    config_text = config_path.read_text(encoding="utf-8")
    config_text = _parse_env_variables(config_text)
    config_data = _parse(config_extension, config_text)
    if cli_overrides:
        _apply_overrides(config_data, cli_overrides)
    values = _flatten_config(config_data)
    return AnnaEngineConfig(**values)
