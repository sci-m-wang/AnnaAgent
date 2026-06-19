import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from anna_agent.model_services import (
    build_vllm_command,
    configure_sft_endpoint,
    deploy_env_status,
    deploy_vllm_service,
    resolve_vllm_command,
    set_sft_mode,
    setup_deploy_env,
    vllm_available,
    wait_for_openai_service,
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


def test_build_vllm_command_accepts_custom_executable(tmp_path: Path):
    command = build_vllm_command(
        vllm_command="/opt/vllm/bin/vllm",
        model_path=tmp_path / "model",
        host="127.0.0.1",
        port=8001,
        api_key="key",
        model_name="complaint",
        gpu_memory_utilization=0.3,
        max_model_len=None,
    )

    assert command[:3] == ["/opt/vllm/bin/vllm", "serve", str(tmp_path / "model")]


def test_vllm_available_supports_absolute_executable(tmp_path: Path):
    executable = tmp_path / "vllm"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")

    assert vllm_available(str(executable)) is True


def test_resolve_vllm_command_prefers_workspace_env(tmp_path: Path):
    initialize_workspace(tmp_path)
    vllm_path = tmp_path / ".anna-deploy-venv" / "bin" / "vllm"
    vllm_path.parent.mkdir(parents=True)
    vllm_path.write_text("#!/bin/sh\n", encoding="utf-8")

    assert resolve_vllm_command(tmp_path) == str(vllm_path)


def test_setup_deploy_env_runs_uv_commands(tmp_path: Path, monkeypatch):
    calls = []

    def fake_run(command, check):
        calls.append(command)
        if command[1] == "venv":
            bin_dir = tmp_path / ".anna-deploy-venv" / "bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "python").write_text("#!/bin/sh\n", encoding="utf-8")
            (bin_dir / "vllm").write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr(
        "anna_agent.model_services.shutil.which", lambda _: "/usr/bin/uv"
    )
    monkeypatch.setattr("anna_agent.model_services.subprocess.run", fake_run)

    status = setup_deploy_env(tmp_path, python="3.12")

    assert status["available"] is True
    assert calls[0][:4] == ["/usr/bin/uv", "venv", "--python", "3.12"]
    assert calls[1][:4] == ["/usr/bin/uv", "pip", "install", "--python"]


def test_deploy_env_status_reports_workspace_paths(tmp_path: Path):
    status = deploy_env_status(tmp_path)

    assert status["path"] == str(tmp_path / ".anna-deploy-venv")
    assert status["vllm"].endswith(".anna-deploy-venv/bin/vllm")


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


def test_deploy_vllm_dry_run_uses_workspace_vllm(tmp_path: Path):
    initialize_workspace(tmp_path)
    vllm_path = tmp_path / ".anna-deploy-venv" / "bin" / "vllm"
    vllm_path.parent.mkdir(parents=True)
    vllm_path.write_text("#!/bin/sh\n", encoding="utf-8")

    result = deploy_vllm_service(
        tmp_path,
        target="complaint",
        model_path=tmp_path / "missing-model",
        dry_run=True,
        pull=False,
    )

    assert result["command"][0] == str(vllm_path)


def test_wait_for_openai_service_accepts_models_response(monkeypatch):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        "anna_agent.model_services.urllib.request.urlopen",
        lambda request, timeout: FakeResponse(),
    )

    wait_for_openai_service(base_url="http://127.0.0.1:9001/v1", api_key="key")


def test_wait_for_openai_service_reports_exited_process_log(tmp_path: Path):
    log_path = tmp_path / "service.log"
    log_path.write_text("first\nlast failure\n", encoding="utf-8")

    class FakeProcess:
        returncode = 1

        def poll(self):
            return 1

    with pytest.raises(RuntimeError) as exc_info:
        wait_for_openai_service(
            base_url="http://127.0.0.1:9001/v1",
            api_key="key",
            process=FakeProcess(),
            log_path=log_path,
        )

    assert "process exited" in str(exc_info.value)
    assert "last failure" in str(exc_info.value)


def test_wait_for_openai_service_reports_progress(monkeypatch):
    progress = []

    def fake_urlopen(request, timeout):
        raise OSError("connection refused")

    def fake_sleep(interval):
        raise RuntimeError("stop")

    monkeypatch.setattr(
        "anna_agent.model_services.urllib.request.urlopen", fake_urlopen
    )
    monkeypatch.setattr("anna_agent.model_services.time.sleep", fake_sleep)

    with pytest.raises(RuntimeError, match="stop"):
        wait_for_openai_service(
            base_url="http://127.0.0.1:9001/v1",
            api_key="key",
            progress_callback=progress.append,
        )

    assert progress[0]["base_url"] == "http://127.0.0.1:9001/v1"
    assert "connection refused" in progress[0]["last_error"]


def test_deploy_vllm_waits_before_writing_config(tmp_path: Path, monkeypatch):
    initialize_workspace(tmp_path)
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    class FakeProcess:
        pid = 123

        def poll(self):
            return None

    wait_calls = []
    monkeypatch.setattr("anna_agent.model_services.vllm_available", lambda _: True)
    monkeypatch.setattr(
        "anna_agent.model_services._start_background",
        lambda workspace, target, command, gpu: FakeProcess(),
    )

    def fake_wait(**kwargs):
        wait_calls.append(kwargs)

    monkeypatch.setattr("anna_agent.model_services.wait_for_openai_service", fake_wait)

    result = deploy_vllm_service(
        tmp_path,
        target="complaint",
        model_path=model_dir,
        port=9001,
        model_name="complaint-local",
        wait_timeout=7,
        pull=False,
    )

    settings = yaml.safe_load((tmp_path / "settings.yaml").read_text())
    assert result["pid"] == 123
    assert wait_calls[0]["base_url"] == "http://127.0.0.1:9001/v1"
    assert wait_calls[0]["timeout"] == 7
    assert settings["servers"]["complaint"]["base_url"] == "http://127.0.0.1:9001/v1"
    assert settings["servers"]["complaint"]["model_name"] == "complaint-local"


def test_deploy_vllm_does_not_write_config_when_wait_fails(tmp_path: Path, monkeypatch):
    initialize_workspace(tmp_path)
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    class FakeProcess:
        pid = 123

        def poll(self):
            return None

    monkeypatch.setattr("anna_agent.model_services.vllm_available", lambda _: True)
    monkeypatch.setattr(
        "anna_agent.model_services._start_background",
        lambda workspace, target, command, gpu: FakeProcess(),
    )
    monkeypatch.setattr(
        "anna_agent.model_services.wait_for_openai_service",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("not ready")),
    )

    with pytest.raises(RuntimeError):
        deploy_vllm_service(
            tmp_path,
            target="complaint",
            model_path=model_dir,
            port=9001,
            model_name="bad-model",
            pull=False,
        )

    settings = yaml.safe_load((tmp_path / "settings.yaml").read_text())
    assert settings["servers"]["complaint"]["model_name"] == "complaint"


def test_deploy_vllm_uses_manifest_absolute_target(tmp_path: Path):
    initialize_workspace(tmp_path)
    absolute_target = tmp_path / "external" / "complaint-model"
    manifest = {
        "schema_version": 1,
        "assets": [
            {
                "name": "complaint-sft",
                "kind": "model",
                "target": str(absolute_target),
                "source": {
                    "type": "huggingface",
                    "repo_id": "sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct",
                    "repo_type": "model",
                    "revision": "main",
                },
            }
        ],
    }
    manifest_path = tmp_path / "assets" / "anna-assets.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = deploy_vllm_service(
        tmp_path,
        target="complaint",
        dry_run=True,
        pull=False,
    )

    assert result["model_path"] == str(absolute_target)
    assert str(absolute_target) in result["command"]
