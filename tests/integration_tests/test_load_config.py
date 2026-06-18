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
    use_sft_model: false
    model_name: cm
    api_key: ckey
    base_url: https://c.example.com
  counselor:
    api_key: cokey
    base_url: https://co.example.com
  emotion:
    use_sft_model: false
    model_name: em
    api_key: ekey
    base_url: https://e.example.com
memory:
  enabled: true
  auto_index: false
  db_path: .memory/db
  table_name: chunks
  top_k: 12
  window_size: 6
  window_stride: 3
embedding:
  model_name: embed-model
  dimension: 32
  api_key: embed-key
  base_url: https://embed.example.com
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.model_name == "test-model"
    assert config.complaint_base_url == "https://c.example.com"
    assert config.counselor_api_key == "cokey"
    assert config.complaint_model_name == "cm"
    assert config.emotion_model_name == "em"
    assert config.complaint_use_sft_model is False
    assert config.emotion_use_sft_model is False
    assert config.active_complaint_model_name == "test-model"
    assert config.active_emotion_model_name == "test-model"
    assert config.memory_auto_index is False
    assert config.memory_db_path == ".memory/db"
    assert config.memory_top_k == 12
    assert config.memory_window_size == 6
    assert config.memory_window_stride == 3
    assert config.embedding_model_name == "embed-model"
    assert config.embedding_dimension == 32


def test_load_config_embedding_env_aliases(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: test-model
  api_key: key
  base_url: https://example.com
embedding:
  model_name: text-embedding-3-small
  dimension: 1536
  api_key: ""
  base_url: ""
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "real-embed-model")
    monkeypatch.setenv("OPENAI_EMBEDDING_API_KEY", "real-embed-key")
    monkeypatch.setenv("OPENAI_EMBEDDING_BASE_URL", "https://embed.example.com/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_DIMENSION", "1024")

    config = load_config(tmp_path)

    assert config.embedding_model_name == "real-embed-model"
    assert config.embedding_api_key == "real-embed-key"
    assert config.embedding_base_url == "https://embed.example.com/v1"
    assert config.embedding_dimension == 1024
