from dataclasses import dataclass


@dataclass
class AnnaEngineDefaults:
    """Default engine configuration values."""

    model_name: str = "counselor"
    api_key: str = "counselor"
    base_url: str = "http://localhost:8002/v1"

    complaint_api_key: str = "complaint_chain"
    counselor_api_key: str = "counselor"
    emotion_api_key: str = "emotion_inferencer"

    complaint_use_sft_model: bool = True
    emotion_use_sft_model: bool = True

    complaint_model_name: str = "complaint"
    counselor_model_name: str = "counselor"
    emotion_model_name: str = "emotion"

    complaint_base_url: str = "http://localhost:8001/v1"
    counselor_base_url: str = "http://localhost:8002/v1"
    emotion_base_url: str = "http://localhost:8000/v1"

    memory_enabled: bool = True
    memory_auto_index: bool = True
    memory_db_path: str = ".anna_memory/lancedb"
    memory_table_name: str = "memory_chunks"
    memory_top_k: int = 8
    memory_window_size: int = 4
    memory_window_stride: int = 2

    embedding_model_name: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    embedding_api_key: str = ""
    embedding_base_url: str = ""


anna_engine_defaults = AnnaEngineDefaults()
