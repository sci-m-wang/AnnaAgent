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
            "complaint": {"api_key": "c", "base_url": "cu"},
            "counselor": {"api_key": "co", "base_url": "cou"},
            "emotion": {"api_key": "e", "base_url": "eu"},
        },
    }
    result = _flatten_config(src)
    assert result == {
        "model_name": "m",
        "api_key": "k",
        "base_url": "u",
        "complaint_api_key": "c",
        "complaint_base_url": "cu",
        "counselor_api_key": "co",
        "counselor_base_url": "cou",
        "emotion_api_key": "e",
        "emotion_base_url": "eu",
    }
