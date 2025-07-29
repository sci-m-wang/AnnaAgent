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
    api_key: ck
    base_url: https://c.example.com
    model_name: cm
  counselor:
    api_key: cok
    base_url: https://co.example.com
  emotion:
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
