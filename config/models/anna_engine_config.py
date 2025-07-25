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
    complaint_server: str = Field(default=anna_engine_defaults.complaint_server)
    counselor_server: str = Field(default=anna_engine_defaults.counselor_server)
    emotion_server: str = Field(default=anna_engine_defaults.emotion_server)

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
            "complaint_server": pref(
                "COMPLAINT_SERVER", anna_engine_defaults.complaint_server
            ),
            "counselor_server": pref(
                "COUNSELOR_SERVER", anna_engine_defaults.counselor_server
            ),
            "emotion_server": pref(
                "EMOTION_SERVER", anna_engine_defaults.emotion_server
            ),
        }
        return cls(**values)
