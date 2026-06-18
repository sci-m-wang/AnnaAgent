import json
import os
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import load_dotenv

from .defaults import anna_engine_defaults
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


def _get_config_path(root_dir: Path) -> Path:
    config_path = _search_for_config_in_root_dir(root_dir)
    if not config_path:
        raise FileNotFoundError(
            f"Config file not found in root directory: {root_dir}"
        )
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
                message = f"data[{current_path}] is not a dict"
                raise TypeError(
                    f"Cannot override non-dict value: {message}."
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
    if model_service.get("model_name") is not None:
        values["model_name"] = model_service.get("model_name")
    if model_service.get("api_key") is not None:
        values["api_key"] = model_service.get("api_key")
    if model_service.get("base_url") is not None:
        values["base_url"] = model_service.get("base_url")

    servers = data.get("servers") or {}
    complaint = servers.get("complaint") or {}
    if complaint.get("api_key") is not None:
        values["complaint_api_key"] = complaint.get("api_key")
    if complaint.get("base_url") is not None:
        values["complaint_base_url"] = complaint.get("base_url")
    if complaint.get("model_name") is not None:
        values["complaint_model_name"] = complaint.get("model_name")
    if complaint.get("use_sft_model") is not None:
        values["complaint_use_sft_model"] = complaint.get("use_sft_model")

    counselor = servers.get("counselor") or {}
    if counselor.get("api_key") is not None:
        values["counselor_api_key"] = counselor.get("api_key")
    if counselor.get("base_url") is not None:
        values["counselor_base_url"] = counselor.get("base_url")
    if counselor.get("model_name") is not None:
        values["counselor_model_name"] = counselor.get("model_name")

    emotion = servers.get("emotion") or {}
    if emotion.get("api_key") is not None:
        values["emotion_api_key"] = emotion.get("api_key")
    if emotion.get("base_url") is not None:
        values["emotion_base_url"] = emotion.get("base_url")
    if emotion.get("model_name") is not None:
        values["emotion_model_name"] = emotion.get("model_name")
    if emotion.get("use_sft_model") is not None:
        values["emotion_use_sft_model"] = emotion.get("use_sft_model")

    memory = data.get("memory") or {}
    if memory.get("enabled") is not None:
        values["memory_enabled"] = memory.get("enabled")
    if memory.get("auto_index") is not None:
        values["memory_auto_index"] = memory.get("auto_index")
    if memory.get("db_path") is not None:
        values["memory_db_path"] = memory.get("db_path")
    if memory.get("table_name") is not None:
        values["memory_table_name"] = memory.get("table_name")
    if memory.get("top_k") is not None:
        values["memory_top_k"] = memory.get("top_k")
    if memory.get("window_size") is not None:
        values["memory_window_size"] = memory.get("window_size")
    if memory.get("window_stride") is not None:
        values["memory_window_stride"] = memory.get("window_stride")

    embedding = data.get("embedding") or {}
    if embedding.get("model_name") is not None:
        values["embedding_model_name"] = embedding.get("model_name")
    if embedding.get("dimension") is not None:
        values["embedding_dimension"] = embedding.get("dimension")
    if embedding.get("api_key") is not None:
        values["embedding_api_key"] = embedding.get("api_key")
    if embedding.get("base_url") is not None:
        values["embedding_base_url"] = embedding.get("base_url")
    return values


def _first_env(*keys: str) -> str | None:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def _apply_embedding_env_aliases(values: dict[str, Any]) -> None:
    api_key = _first_env("OPENAI_EMBEDDING_API_KEY", "EMBEDDING_API_KEY")
    base_url = _first_env("OPENAI_EMBEDDING_BASE_URL", "EMBEDDING_BASE_URL")
    model_name = _first_env(
        "OPENAI_EMBEDDING_MODEL",
        "OPENAI_EMBEDDING_MODEL_NAME",
        "EMBEDDING_MODEL",
        "EMBEDDING_MODEL_NAME",
    )
    dimension = _first_env("OPENAI_EMBEDDING_DIMENSION", "EMBEDDING_DIMENSION")

    if api_key and not values.get("embedding_api_key"):
        values["embedding_api_key"] = api_key
    if base_url and not values.get("embedding_base_url"):
        values["embedding_base_url"] = base_url
    if model_name and values.get("embedding_model_name") in {
        None,
        anna_engine_defaults.embedding_model_name,
    }:
        values["embedding_model_name"] = model_name
    if dimension and values.get("embedding_dimension") in {
        None,
        anna_engine_defaults.embedding_dimension,
    }:
        values["embedding_dimension"] = int(dimension)


def load_config(
    root_dir: Path,
    cli_overrides: dict[str, Any] | None = None,
) -> AnnaEngineConfig:
    root = root_dir.resolve()
    config_path = _get_config_path(root)
    _load_dotenv(config_path)
    config_extension = config_path.suffix
    config_text = config_path.read_text(encoding="utf-8")
    config_text = _parse_env_variables(config_text)
    config_data = _parse(config_extension, config_text)
    if cli_overrides:
        _apply_overrides(config_data, cli_overrides)
    values = _flatten_config(config_data)
    _apply_embedding_env_aliases(values)
    return AnnaEngineConfig(**values)
