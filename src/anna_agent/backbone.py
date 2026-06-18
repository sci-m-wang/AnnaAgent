"""Load base OpenAI configuration for the OpenAI clients."""

from pathlib import Path
import os

from openai import OpenAI

from .config import AnnaEngineConfig, load_config
from .common.registry import registry


def _load_engine_config(workspace: Path | None = None) -> AnnaEngineConfig:
    """Load the engine configuration.

    The function first attempts to load ``settings.yaml`` using :func:`load_config`.
    ``workspace`` can be passed explicitly or is read from the ``ANNA_AGENT_WORKSPACE``
    environment variable. If no configuration file is found, the function falls
    back to loading values from the environment via :meth:`AnnaEngineConfig.load`.
    """

    root = Path(
        workspace if workspace is not None else os.getenv("ANNA_AGENT_WORKSPACE", Path.cwd())
    )
    try:
        return load_config(root)
    except FileNotFoundError:  # pragma: no cover - optional fallback
        return AnnaEngineConfig.load(root)


def configure(workspace: Path | None = None) -> None:
    """(Re)load configuration from ``workspace`` and update globals."""

    root = Path(workspace if workspace is not None else os.getenv("ANNA_AGENT_WORKSPACE", Path.cwd()))
    cfg = _load_engine_config(workspace)
    # Register configuration for global access
    registry.register("anna_engine_config", cfg)
    registry.register("anna_agent_workspace", root)
    globals().update(
        {
            "api_key": cfg.api_key,
            "base_url": cfg.base_url,
            "complaint_api_key": cfg.complaint_api_key,
            "counselor_api_key": cfg.counselor_api_key,
            "emotion_api_key": cfg.emotion_api_key,
            "complaint_use_sft_model": cfg.complaint_use_sft_model,
            "emotion_use_sft_model": cfg.emotion_use_sft_model,
            "complaint_model_name": cfg.complaint_model_name,
            "counselor_model_name": cfg.counselor_model_name,
            "emotion_model_name": cfg.emotion_model_name,
            "complaint_base_url": cfg.complaint_base_url,
            "counselor_base_url": cfg.counselor_base_url,
            "emotion_base_url": cfg.emotion_base_url,
            "memory_enabled": cfg.memory_enabled,
            "memory_auto_index": cfg.memory_auto_index,
            "memory_db_path": cfg.memory_db_path,
            "memory_table_name": cfg.memory_table_name,
            "memory_top_k": cfg.memory_top_k,
            "memory_window_size": cfg.memory_window_size,
            "memory_window_stride": cfg.memory_window_stride,
            "embedding_model_name": cfg.embedding_model_name,
            "embedding_dimension": cfg.embedding_dimension,
            "embedding_api_key": cfg.embedding_api_key,
            "embedding_base_url": cfg.embedding_base_url,
        }
    )


def get_openai_client(
    api_key_override: str | None = None, base_url_override: str | None = None
) -> OpenAI:
    """Create an OpenAI client using configuration values."""
    cfg = registry.get("anna_engine_config")
    return OpenAI(
        api_key=api_key_override or cfg.api_key,
        base_url=base_url_override or cfg.base_url,
    )


def get_complaint_client() -> OpenAI:
    """Create a client for the complaint server."""
    cfg = registry.get("anna_engine_config")
    if not cfg.complaint_use_sft_model:
        return get_openai_client()
    return get_openai_client(cfg.complaint_api_key, cfg.complaint_base_url)


def get_counselor_client() -> OpenAI:
    """Create a client for the counselor server."""
    cfg = registry.get("anna_engine_config")
    return get_openai_client(cfg.counselor_api_key, cfg.counselor_base_url)


def get_emotion_client() -> OpenAI:
    """Create a client for the emotion server."""
    cfg = registry.get("anna_engine_config")
    if not cfg.emotion_use_sft_model:
        return get_openai_client()
    return get_openai_client(cfg.emotion_api_key, cfg.emotion_base_url)
