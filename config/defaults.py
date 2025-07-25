from dataclasses import dataclass

@dataclass
class AnnaEngineDefaults:
    """Default engine configuration values."""

    model_name: str = "counselor"
    api_key: str = "counselor"
    base_url: str = "http://localhost:8002/v1"
    complaint_server: str = "bash complaint.sh"
    counselor_server: str = "bash counselor.sh"
    emotion_server: str = "bash emotion.sh"

anna_engine_defaults = AnnaEngineDefaults()
