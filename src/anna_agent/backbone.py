"""Load base OpenAI configuration for the OpenAI clients."""

from pathlib import Path
import os

from openai import OpenAI

from .config import AnnaEngineConfig, load_config


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

    cfg = _load_engine_config(workspace)
    global model_name, api_key, base_url
    global complaint_api_key, counselor_api_key, emotion_api_key
    global complaint_base_url, counselor_base_url, emotion_base_url
    global complaint_model_name, emotion_model_name

    model_name = cfg.model_name
    api_key = cfg.api_key
    base_url = cfg.base_url
    complaint_api_key = cfg.complaint_api_key
    counselor_api_key = cfg.counselor_api_key
    emotion_api_key = cfg.emotion_api_key
    complaint_base_url = cfg.complaint_base_url
    counselor_base_url = cfg.counselor_base_url
    emotion_base_url = cfg.emotion_base_url
    complaint_model_name = cfg.complaint_model_name
    emotion_model_name = cfg.emotion_model_name


def get_openai_client(
    api_key_override: str | None = None, base_url_override: str | None = None
) -> OpenAI:
    """Create an OpenAI client using configuration values."""
    return OpenAI(
        api_key=api_key_override or api_key, base_url=base_url_override or base_url
    )


def get_complaint_client() -> OpenAI:
    """Create a client for the complaint server."""
    return get_openai_client(complaint_api_key, complaint_base_url)


def get_counselor_client() -> OpenAI:
    """Create a client for the counselor server."""
    return get_openai_client(counselor_api_key, counselor_base_url)


def get_emotion_client() -> OpenAI:
    """Create a client for the emotion server."""
    return get_openai_client(emotion_api_key, emotion_base_url)
