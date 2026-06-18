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
    complaint_api_key: str = Field(default=anna_engine_defaults.complaint_api_key)
    counselor_api_key: str = Field(default=anna_engine_defaults.counselor_api_key)
    emotion_api_key: str = Field(default=anna_engine_defaults.emotion_api_key)
    complaint_use_sft_model: bool = Field(
        default=anna_engine_defaults.complaint_use_sft_model
    )
    emotion_use_sft_model: bool = Field(
        default=anna_engine_defaults.emotion_use_sft_model
    )
    complaint_model_name: str = Field(
        default=anna_engine_defaults.complaint_model_name
    )
    counselor_model_name: str = Field(
        default=anna_engine_defaults.counselor_model_name
    )
    emotion_model_name: str = Field(
        default=anna_engine_defaults.emotion_model_name
    )
    complaint_base_url: str = Field(default=anna_engine_defaults.complaint_base_url)
    counselor_base_url: str = Field(default=anna_engine_defaults.counselor_base_url)
    emotion_base_url: str = Field(default=anna_engine_defaults.emotion_base_url)

    @property
    def active_complaint_model_name(self) -> str:
        return (
            self.complaint_model_name
            if self.complaint_use_sft_model
            else self.model_name
        )

    @property
    def active_emotion_model_name(self) -> str:
        return (
            self.emotion_model_name
            if self.emotion_use_sft_model
            else self.model_name
        )

    @classmethod
    def load(cls, root_dir: str | Path | None = None) -> "AnnaEngineConfig":
        env = Env()
        env_path = Path(root_dir) / ".env" if root_dir else Path(".env")
        if env_path.exists():
            env.read_env(env_path)
        else:
            env.read_env()
        reader = EnvironmentReader(env)
        with reader.envvar_prefix("ANNA_ENGINE"):
            values = {
                "model_name": reader.str(
                    "MODEL_NAME",
                    default_value=anna_engine_defaults.model_name,
                ),
                "api_key": reader.str(
                    "API_KEY", default_value=anna_engine_defaults.api_key
                ),
                "base_url": reader.str(
                    "BASE_URL", default_value=anna_engine_defaults.base_url
                ),
                "complaint_api_key": reader.str(
                    "COMPLAINT_API_KEY",
                    default_value=anna_engine_defaults.complaint_api_key,
                ),
                "counselor_api_key": reader.str(
                    "COUNSELOR_API_KEY",
                    default_value=anna_engine_defaults.counselor_api_key,
                ),
                "emotion_api_key": reader.str(
                    "EMOTION_API_KEY",
                    default_value=anna_engine_defaults.emotion_api_key,
                ),
                "complaint_base_url": reader.str(
                    "COMPLAINT_BASE_URL",
                    default_value=anna_engine_defaults.complaint_base_url,
                ),
                "complaint_use_sft_model": reader.bool(
                    "COMPLAINT_USE_SFT_MODEL",
                    default_value=anna_engine_defaults.complaint_use_sft_model,
                ),
                "counselor_base_url": reader.str(
                    "COUNSELOR_BASE_URL",
                    default_value=anna_engine_defaults.counselor_base_url,
                ),
                "emotion_base_url": reader.str(
                    "EMOTION_BASE_URL",
                    default_value=anna_engine_defaults.emotion_base_url,
                ),
                "emotion_use_sft_model": reader.bool(
                    "EMOTION_USE_SFT_MODEL",
                    default_value=anna_engine_defaults.emotion_use_sft_model,
                ),
                "complaint_model_name": reader.str(
                    "COMPLAINT_MODEL_NAME",
                    default_value=anna_engine_defaults.complaint_model_name,
                ),
                "counselor_model_name": reader.str(
                    "COUNSELOR_MODEL_NAME",
                    default_value=anna_engine_defaults.counselor_model_name,
                ),
                "emotion_model_name": reader.str(
                    "EMOTION_MODEL_NAME",
                    default_value=anna_engine_defaults.emotion_model_name,
                ),
            }
        mimo_model = env("MIMO_MODEL", None)
        mimo_api_key = env("MIMO_API_KEY", None)
        mimo_base_url = env("MIMO_BASE_URL", None)
        if values["model_name"] == anna_engine_defaults.model_name and mimo_model:
            values["model_name"] = mimo_model
        if values["api_key"] == anna_engine_defaults.api_key and mimo_api_key:
            values["api_key"] = mimo_api_key
        if values["base_url"] == anna_engine_defaults.base_url and mimo_base_url:
            values["base_url"] = mimo_base_url
        if (
            values["counselor_model_name"]
            == anna_engine_defaults.counselor_model_name
            and mimo_model
        ):
            values["counselor_model_name"] = mimo_model
        if (
            values["counselor_api_key"] == anna_engine_defaults.counselor_api_key
            and mimo_api_key
        ):
            values["counselor_api_key"] = mimo_api_key
        if (
            values["counselor_base_url"] == anna_engine_defaults.counselor_base_url
            and mimo_base_url
        ):
            values["counselor_base_url"] = mimo_base_url
        return cls(**values)
