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
    memory_enabled: bool = Field(default=anna_engine_defaults.memory_enabled)
    memory_auto_index: bool = Field(default=anna_engine_defaults.memory_auto_index)
    memory_db_path: str = Field(default=anna_engine_defaults.memory_db_path)
    memory_table_name: str = Field(default=anna_engine_defaults.memory_table_name)
    memory_top_k: int = Field(default=anna_engine_defaults.memory_top_k)
    memory_window_size: int = Field(default=anna_engine_defaults.memory_window_size)
    memory_window_stride: int = Field(default=anna_engine_defaults.memory_window_stride)
    embedding_model_name: str = Field(default=anna_engine_defaults.embedding_model_name)
    embedding_dimension: int = Field(default=anna_engine_defaults.embedding_dimension)
    embedding_api_key: str = Field(default=anna_engine_defaults.embedding_api_key)
    embedding_base_url: str = Field(default=anna_engine_defaults.embedding_base_url)

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
                "memory_enabled": reader.bool(
                    "MEMORY_ENABLED",
                    default_value=anna_engine_defaults.memory_enabled,
                ),
                "memory_auto_index": reader.bool(
                    "MEMORY_AUTO_INDEX",
                    default_value=anna_engine_defaults.memory_auto_index,
                ),
                "memory_db_path": reader.str(
                    "MEMORY_DB_PATH",
                    default_value=anna_engine_defaults.memory_db_path,
                ),
                "memory_table_name": reader.str(
                    "MEMORY_TABLE_NAME",
                    default_value=anna_engine_defaults.memory_table_name,
                ),
                "memory_top_k": reader.int(
                    "MEMORY_TOP_K",
                    default_value=anna_engine_defaults.memory_top_k,
                ),
                "memory_window_size": reader.int(
                    "MEMORY_WINDOW_SIZE",
                    default_value=anna_engine_defaults.memory_window_size,
                ),
                "memory_window_stride": reader.int(
                    "MEMORY_WINDOW_STRIDE",
                    default_value=anna_engine_defaults.memory_window_stride,
                ),
                "embedding_model_name": reader.str(
                    "EMBEDDING_MODEL_NAME",
                    default_value=anna_engine_defaults.embedding_model_name,
                ),
                "embedding_dimension": reader.int(
                    "EMBEDDING_DIMENSION",
                    default_value=anna_engine_defaults.embedding_dimension,
                ),
                "embedding_api_key": reader.str(
                    "EMBEDDING_API_KEY",
                    default_value=anna_engine_defaults.embedding_api_key,
                ),
                "embedding_base_url": reader.str(
                    "EMBEDDING_BASE_URL",
                    default_value=anna_engine_defaults.embedding_base_url,
                ),
            }
        mimo_model = env("MIMO_MODEL", None)
        mimo_api_key = env("MIMO_API_KEY", None)
        mimo_base_url = env("MIMO_BASE_URL", None)
        embedding_model = env("OPENAI_EMBEDDING_MODEL", None) or env(
            "OPENAI_EMBEDDING_MODEL_NAME", None
        ) or env("EMBEDDING_MODEL", None) or env("EMBEDDING_MODEL_NAME", None)
        embedding_api_key = env("OPENAI_EMBEDDING_API_KEY", None) or env(
            "EMBEDDING_API_KEY", None
        )
        embedding_base_url = env("OPENAI_EMBEDDING_BASE_URL", None) or env(
            "EMBEDDING_BASE_URL", None
        )
        embedding_dimension = env("OPENAI_EMBEDDING_DIMENSION", None) or env(
            "EMBEDDING_DIMENSION", None
        )
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
        counselor_defaults = {
            "counselor_api_key": anna_engine_defaults.counselor_api_key,
            "counselor_base_url": anna_engine_defaults.counselor_base_url,
            "counselor_model_name": anna_engine_defaults.counselor_model_name,
        }
        if all(
            values[field] == default for field, default in counselor_defaults.items()
        ):
            values["counselor_api_key"] = values["api_key"]
            values["counselor_base_url"] = values["base_url"]
            values["counselor_model_name"] = values["model_name"]
        if (
            values["embedding_model_name"]
            == anna_engine_defaults.embedding_model_name
            and embedding_model
        ):
            values["embedding_model_name"] = embedding_model
        if not values["embedding_api_key"] and embedding_api_key:
            values["embedding_api_key"] = embedding_api_key
        if not values["embedding_base_url"] and embedding_base_url:
            values["embedding_base_url"] = embedding_base_url
        if (
            values["embedding_dimension"]
            == anna_engine_defaults.embedding_dimension
            and embedding_dimension
        ):
            values["embedding_dimension"] = int(embedding_dimension)
        return cls(**values)
