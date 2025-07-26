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

    complaint_base_url: str = "http://localhost:8001/v1"
    counselor_base_url: str = "http://localhost:8002/v1"
    emotion_base_url: str = "http://localhost:8000/v1"


anna_engine_defaults = AnnaEngineDefaults()
