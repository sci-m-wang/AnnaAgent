import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from anna_agent.config.load_config import load_config


def test_load_config(tmp_path: Path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: test-model
  api_key: key
  base_url: https://example.com
servers:
  complaint:
    model_name: cm
    api_key: ckey
    base_url: https://c.example.com
  counselor:
    api_key: cokey
    base_url: https://co.example.com
  emotion:
    model_name: em
    api_key: ekey
    base_url: https://e.example.com
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.model_name == "test-model"
    assert config.complaint_base_url == "https://c.example.com"
    assert config.counselor_api_key == "cokey"
    assert config.complaint_model_name == "cm"
    assert config.emotion_model_name == "em"
