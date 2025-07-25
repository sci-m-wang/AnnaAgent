"""Load base OpenAI configuration from environment."""

from openai import OpenAI

from config import AnnaEngineConfig

_cfg = AnnaEngineConfig.load()

model_name: str = _cfg.model_name
api_key: str = _cfg.api_key
base_url: str = _cfg.base_url


def get_openai_client(api_key_override: str | None = None, base_url_override: str | None = None) -> OpenAI:
    """Create an OpenAI client using configuration values."""
    return OpenAI(api_key=api_key_override or api_key, base_url=base_url_override or base_url)
