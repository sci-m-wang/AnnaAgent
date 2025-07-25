from pathlib import Path

from environs import Env
from pydantic import BaseModel, Field

from ..defaults import anna_engine_defaults
from ..environment_reader import EnvironmentReader


class AnnaEngineConfig(BaseModel):
    """Minimal configuration loaded from environment."""

    model_name: str = Field(default=anna_engine_defaults.model_name)
    api_key: str = Field(default=anna_engine_defaults.api_key)
    base_url: str = Field(default=anna_engine_defaults.base_url)
    complaint_api_key: str = Field(
        default=anna_engine_defaults.complaint_api_key
    )
    counselor_api_key: str = Field(
        default=anna_engine_defaults.counselor_api_key
    )
    emotion_api_key: str = Field(
        default=anna_engine_defaults.emotion_api_key
    )
    complaint_base_url: str = Field(
        default=anna_engine_defaults.complaint_base_url
    )
    counselor_base_url: str = Field(
        default=anna_engine_defaults.counselor_base_url
    )
    emotion_base_url: str = Field(default=anna_engine_defaults.emotion_base_url)

    @classmethod
    def load(cls, root_dir: str | Path | None = None) -> "AnnaEngineConfig":
        env = Env()
        env_path = Path(root_dir) / ".env" if root_dir else Path(".env")
        if env_path.exists():
            env.read_env(env_path)
        else:
            env.read_env()
        reader = EnvironmentReader(env)
        pref = reader.envvar_prefix("ANNA_ENGINE")
        values = {
            "model_name": pref("MODEL_NAME", anna_engine_defaults.model_name),
            "api_key": pref("API_KEY", anna_engine_defaults.api_key),
            "base_url": pref("BASE_URL", anna_engine_defaults.base_url),
            "complaint_api_key": pref(
                "COMPLAINT_API_KEY", anna_engine_defaults.complaint_api_key
            ),
            "counselor_api_key": pref(
                "COUNSELOR_API_KEY", anna_engine_defaults.counselor_api_key
            ),
            "emotion_api_key": pref(
                "EMOTION_API_KEY", anna_engine_defaults.emotion_api_key
            ),
            "complaint_base_url": pref(
                "COMPLAINT_BASE_URL", anna_engine_defaults.complaint_base_url
            ),
            "counselor_base_url": pref(
                "COUNSELOR_BASE_URL", anna_engine_defaults.counselor_base_url
            ),
            "emotion_base_url": pref(
                "EMOTION_BASE_URL", anna_engine_defaults.emotion_base_url
            ),
        }
        return cls(**values)
