import importlib
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def test_backbone_loads_workspace(tmp_path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: my-model
  api_key: key
  base_url: https://example.com
servers:
  complaint:
    use_sft_model: false
    api_key: ck
    base_url: https://c.example.com
    model_name: cm
  counselor:
    api_key: cok
    base_url: https://co.example.com
  emotion:
    use_sft_model: true
    api_key: ek
    base_url: https://e.example.com
    model_name: em
""",
        encoding="utf-8",
    )
    mod = importlib.import_module("anna_agent.backbone")
    mod.configure(tmp_path)
    assert mod.base_url == "https://example.com"
    assert mod.complaint_base_url == "https://c.example.com"
    assert mod.counselor_api_key == "cok"
    assert mod.emotion_api_key == "ek"
    from anna_agent.common.registry import registry
    cfg = registry.get("anna_engine_config")
    assert cfg.base_url == "https://example.com"
    assert cfg.complaint_api_key == "ck"
    assert cfg.complaint_use_sft_model is False
    assert cfg.emotion_use_sft_model is True
    assert cfg.active_complaint_model_name == "my-model"
    assert cfg.active_emotion_model_name == "em"
