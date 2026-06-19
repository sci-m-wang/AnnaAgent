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


def test_load_config_uses_dotenv_secret_placeholders(tmp_path: Path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: counselor
  api_key: counselor
  base_url: http://localhost:8002/v1
embedding:
  model_name: text-embedding-3-small
  dimension: 1536
  api_key: ""
  base_url: ""
""",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        """
ANNA_ENGINE_API_KEY=base-secret
ANNA_ENGINE_EMBEDDING_API_KEY=embed-secret
ANNA_ENGINE_EMBEDDING_BASE_URL=https://embed.example.com/v1
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.api_key == "base-secret"
    assert config.embedding_api_key == "embed-secret"
    assert config.embedding_base_url == "https://embed.example.com/v1"


def test_load_config_default_counselor_inherits_base_env_aliases(
    tmp_path: Path, monkeypatch
):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: counselor
  api_key: counselor
  base_url: http://localhost:8002/v1
servers:
  counselor:
    model_name: counselor
    api_key: counselor
    base_url: http://localhost:8002/v1
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("ANNA_ENGINE_MODEL_NAME", raising=False)
    monkeypatch.delenv("ANNA_ENGINE_API_KEY", raising=False)
    monkeypatch.delenv("ANNA_ENGINE_BASE_URL", raising=False)
    monkeypatch.setenv("MIMO_MODEL", "base-chat")
    monkeypatch.setenv("MIMO_API_KEY", "base-secret")
    monkeypatch.setenv("MIMO_BASE_URL", "https://base.example.com/v1")

    config = load_config(tmp_path)

    assert config.model_name == "base-chat"
    assert config.api_key == "base-secret"
    assert config.base_url == "https://base.example.com/v1"
    assert config.counselor_model_name == "base-chat"
    assert config.counselor_api_key == "base-secret"
    assert config.counselor_base_url == "https://base.example.com/v1"


def test_load_config_preserves_explicit_counselor_endpoint(
    tmp_path: Path, monkeypatch
):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
model_service:
  model_name: counselor
  api_key: counselor
  base_url: http://localhost:8002/v1
servers:
  counselor:
    model_name: counselor-custom
    api_key: counselor-secret
    base_url: https://counselor.example.com/v1
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANNA_ENGINE_MODEL_NAME", "base-chat")
    monkeypatch.setenv("ANNA_ENGINE_API_KEY", "base-secret")
    monkeypatch.setenv("ANNA_ENGINE_BASE_URL", "https://base.example.com/v1")

    config = load_config(tmp_path)

    assert config.model_name == "base-chat"
    assert config.counselor_model_name == "counselor-custom"
    assert config.counselor_api_key == "counselor-secret"
    assert config.counselor_base_url == "https://counselor.example.com/v1"
