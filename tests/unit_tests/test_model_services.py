import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from anna_agent.model_services import (
    build_vllm_command,
    configure_sft_endpoint,
    deploy_vllm_service,
    set_sft_mode,
)
from anna_agent.workspace import initialize_workspace


def test_set_sft_mode_updates_both_targets(tmp_path: Path):
    initialize_workspace(tmp_path)

    changed = set_sft_mode(tmp_path, target="all", use_sft=False)

    settings = yaml.safe_load((tmp_path / "settings.yaml").read_text())
    assert changed == ["complaint", "emotion"]
    assert settings["servers"]["complaint"]["use_sft_model"] is False
    assert settings["servers"]["emotion"]["use_sft_model"] is False


def test_configure_sft_endpoint_writes_settings_and_dotenv(tmp_path: Path):
    initialize_workspace(tmp_path)

    configure_sft_endpoint(
        tmp_path,
        target="complaint",
        base_url="http://127.0.0.1:9001/v1",
        model_name="complaint-local",
        api_key="secret-key",
    )

    settings = yaml.safe_load((tmp_path / "settings.yaml").read_text())
    dotenv = (tmp_path / ".env").read_text(encoding="utf-8")
    server = settings["servers"]["complaint"]
    assert server["use_sft_model"] is True
    assert server["base_url"] == "http://127.0.0.1:9001/v1"
    assert server["model_name"] == "complaint-local"
    assert server["api_key"] == "complaint_chain"
    assert "ANNA_ENGINE_COMPLAINT_API_KEY=secret-key" in dotenv


def test_build_vllm_command_uses_openai_compatible_args(tmp_path: Path):
    command = build_vllm_command(
        model_path=tmp_path / "model",
        host="127.0.0.1",
        port=8001,
        api_key="key",
        model_name="complaint",
        gpu_memory_utilization=0.3,
        max_model_len=1024,
        extra_args=["--max-num-seqs", "64"],
    )

    assert command[:3] == ["vllm", "serve", str(tmp_path / "model")]
    assert "--api-key" in command
    assert "--served-model-name" in command
    assert "--enable-auto-tool-choice" in command
    assert "--max-model-len" in command
    assert "--max-num-seqs" in command


def test_deploy_vllm_dry_run_does_not_require_files(tmp_path: Path):
    initialize_workspace(tmp_path)

    result = deploy_vllm_service(
        tmp_path,
        target="emotion",
        model_path=tmp_path / "missing-model",
        port=9000,
        api_key="emotion-key",
        dry_run=True,
        pull=False,
    )

    assert result["base_url"] == "http://127.0.0.1:9000/v1"
    assert result["model_name"] == "emotion"
    assert result["api_key"] == "emotion-key"
    assert result["pid"] is None
