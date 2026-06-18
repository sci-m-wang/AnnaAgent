import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


from anna_agent.config.load_config import _apply_overrides, _flatten_config


def test_apply_overrides_nested():
    data = {"a": {"b": {"c": 1}}}
    overrides = {"a.b.c": 2, "a.d": 3}
    _apply_overrides(data, overrides)
    assert data["a"]["b"]["c"] == 2
    assert data["a"]["d"] == 3


def test_flatten_config():
    src = {
        "model_service": {
            "model_name": "m",
            "api_key": "k",
            "base_url": "u",
        },
        "servers": {
            "complaint": {
                "api_key": "c",
                "base_url": "cu",
                "model_name": "cm",
                "use_sft_model": False,
            },
            "counselor": {"api_key": "co", "base_url": "cou"},
            "emotion": {
                "api_key": "e",
                "base_url": "eu",
                "model_name": "em",
                "use_sft_model": True,
            },
        },
        "memory": {
            "enabled": True,
            "auto_index": False,
            "db_path": ".memory/db",
            "table_name": "chunks",
            "top_k": 12,
            "window_size": 6,
            "window_stride": 3,
        },
        "embedding": {
            "model_name": "embed-model",
            "dimension": 32,
            "api_key": "embed-key",
            "base_url": "https://embed.example.com",
        },
    }
    result = _flatten_config(src)
    assert result == {
        "model_name": "m",
        "api_key": "k",
        "base_url": "u",
        "complaint_api_key": "c",
        "complaint_base_url": "cu",
        "complaint_use_sft_model": False,
        "counselor_api_key": "co",
        "counselor_base_url": "cou",
        "emotion_api_key": "e",
        "emotion_base_url": "eu",
        "emotion_use_sft_model": True,
        "complaint_model_name": "cm",
        "emotion_model_name": "em",
        "memory_enabled": True,
        "memory_auto_index": False,
        "memory_db_path": ".memory/db",
        "memory_table_name": "chunks",
        "memory_top_k": 12,
        "memory_window_size": 6,
        "memory_window_stride": 3,
        "embedding_model_name": "embed-model",
        "embedding_dimension": 32,
        "embedding_api_key": "embed-key",
        "embedding_base_url": "https://embed.example.com",
    }
