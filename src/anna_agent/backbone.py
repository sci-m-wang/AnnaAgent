"""Load base OpenAI configuration from environment."""

from openai import OpenAI

from .config import AnnaEngineConfig

_cfg = AnnaEngineConfig.load()

model_name: str = _cfg.model_name
api_key: str = _cfg.api_key
base_url: str = _cfg.base_url
complaint_api_key: str = _cfg.complaint_api_key
counselor_api_key: str = _cfg.counselor_api_key
emotion_api_key: str = _cfg.emotion_api_key
complaint_base_url: str = _cfg.complaint_base_url
counselor_base_url: str = _cfg.counselor_base_url
emotion_base_url: str = _cfg.emotion_base_url
complaint_model_name: str = _cfg.complaint_model_name
emotion_model_name: str = _cfg.emotion_model_name


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
