import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from typer.testing import CliRunner

from anna_agent.assets import manifest_path
from anna_agent.cli import app

runner = CliRunner()


def test_workspace_to_batch_prompt_only_journey(tmp_path: Path):
    workspace = tmp_path / "workspace"

    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    assert (workspace / "settings.yaml").exists()
    assert (workspace / "assets" / "anna-assets.json").exists()
    case_file = workspace / "cases" / "family_stress_case.json"
    assert case_file.exists()

    result = runner.invoke(app, ["assets", "list", "--workspace", str(workspace)])
    assert result.exit_code == 0, result.output
    assert "emotion-sft" in result.output

    result = runner.invoke(app, ["data", "validate", str(case_file)])
    assert result.exit_code == 0, result.output

    state_file = workspace / "prompts" / "case.state.json"
    result = runner.invoke(
        app,
        ["init", "prompt-only", str(case_file), "--out", str(state_file)],
    )
    assert result.exit_code == 0, result.output
    assert "Initialization · prompt-only" in result.output
    assert "Running:" in result.output
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["mode"] == "prompt_only"
    assert state["prompt"]

    out_dir = workspace / "runs" / "batch"
    result = runner.invoke(
        app,
        [
            "run",
            "batch",
            "--workspace",
            str(workspace),
            "--case",
            "cases/*.json",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "summary.jsonl").exists()


def test_create_can_create_deploy_env(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"

    def fake_setup(workspace_path, python="3.12", force=False):
        assert workspace_path == workspace
        assert python == "3.11"
        assert force is True
        return {
            "path": str(workspace / ".anna-deploy-venv"),
            "vllm": str(workspace / ".anna-deploy-venv" / "bin" / "vllm"),
        }

    monkeypatch.setattr("anna_agent.cli.setup_deploy_env", fake_setup)

    result = runner.invoke(
        app,
        [
            "create",
            str(workspace),
            "--deploy-env",
            "--deploy-python",
            "3.11",
            "--deploy-force",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Deploy environment ready" in result.output


def test_assets_download_reports_unconfigured_assets(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    manifest = json.loads(manifest_path(workspace).read_text(encoding="utf-8"))
    manifest["presets"] = {"local-test": ["missing-url"]}
    manifest["assets"] = [
        {
            "name": "missing-url",
            "kind": "dataset",
            "target": "assets/missing-url",
            "source": {"type": "url", "url": ""},
        }
    ]
    manifest_path(workspace).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    result = runner.invoke(
        app,
        ["assets", "download", "local-test", "--workspace", str(workspace)],
    )

    assert result.exit_code == 0, result.output
    assert "unconfigured" in result.output


def test_assets_list_resolves_manifest_absolute_targets(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    manifest = json.loads(manifest_path(workspace).read_text(encoding="utf-8"))
    absolute_target = Path("/tmp/a")
    manifest["assets"] = [
        {
            "name": "emotion-sft",
            "kind": "model",
            "target": str(absolute_target),
            "source": {
                "type": "huggingface",
                "repo_id": "sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct",
                "repo_type": "model",
                "revision": "main",
            },
        }
    ]
    manifest_path(workspace).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    result = runner.invoke(app, ["assets", "list", "--workspace", str(workspace)])

    assert result.exit_code == 0, result.output
    assert str(absolute_target) in result.output


def test_assets_download_target_override_requires_single_asset(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "assets",
            "download",
            "paper",
            "--workspace",
            str(workspace),
            "--target",
            str(tmp_path / "one-target"),
        ],
    )

    assert result.exit_code != 0


def test_config_secrets_writes_hidden_values_to_dotenv(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["config", "secrets", "--workspace", str(workspace)],
        input="base-secret\nembed-secret\n",
    )

    assert result.exit_code == 0, result.output
    dotenv_text = (workspace / ".env").read_text(encoding="utf-8")
    assert "ANNA_ENGINE_API_KEY=base-secret" in dotenv_text
    assert "ANNA_ENGINE_EMBEDDING_API_KEY=embed-secret" in dotenv_text
    assert "base-secret" not in result.output


def test_models_commands_configure_sft_modes(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["models", "use-base", "--workspace", str(workspace), "--target", "all"],
    )
    assert result.exit_code == 0, result.output
    assert "anna test model" in result.output

    result = runner.invoke(
        app,
        [
            "models",
            "configure",
            "--workspace",
            str(workspace),
            "--target",
            "emotion",
            "--base-url",
            "http://127.0.0.1:9000/v1",
            "--model-name",
            "emotion-local",
        ],
        input="emotion-secret\n",
    )
    assert result.exit_code == 0, result.output
    settings = (workspace / "settings.yaml").read_text(encoding="utf-8")
    dotenv = (workspace / ".env").read_text(encoding="utf-8")
    assert "use_sft_model: true" in settings
    assert "http://127.0.0.1:9000/v1" in settings
    assert "model_name: emotion-local" in settings
    assert "ANNA_ENGINE_EMOTION_API_KEY=emotion-secret" in dotenv


def test_models_deploy_dry_run_prints_vllm_command(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "models",
            "deploy",
            "--workspace",
            str(workspace),
            "--target",
            "complaint",
            "--model-path",
            str(tmp_path / "missing-model"),
            "--vllm-command",
            "/opt/vllm/bin/vllm",
            "--port",
            "9001",
            "--gpu",
            "0",
            "--dry-run",
            "--no-download",
        ],
        input="deploy-secret\n",
    )
    assert result.exit_code == 0, result.output
    assert "CUDA_VISIBLE_DEVICES=0 /opt/vllm/bin/vllm serve" in result.output
    assert "--port 9001" in result.output
    assert "deploy-secret" not in result.output
    assert "--api-key ***" in result.output
    assert "Dry run only" in result.output


def test_models_deploy_missing_vllm_reports_concise_error(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "models",
            "deploy",
            "--workspace",
            str(workspace),
            "--target",
            "complaint",
            "--model-path",
            str(model_dir),
            "--vllm-command",
            str(tmp_path / "missing-vllm"),
            "--no-download",
        ],
        input="\n",
    )

    assert result.exit_code == 1
    assert "vLLM is not available" in result.output
    assert "Traceback" not in result.output


def test_models_deploy_wait_progress_redacts_log_secrets(
    tmp_path: Path, monkeypatch
):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    def fake_deploy(workspace_path, **kwargs):
        gpu_callback = kwargs["gpu_preflight_callback"]
        gpu_callback(
            {
                "requested_gpu": kwargs["gpu"],
                "cuda_visible_devices": kwargs["gpu"],
                "gpu_memory_utilization": kwargs["gpu_memory_utilization"],
                "devices": [
                    {
                        "index": 1,
                        "name": "NVIDIA A100",
                        "memory_total_mib": 81920,
                        "memory_free_mib": 79872,
                        "vllm_cap_mib": 69632,
                    }
                ],
                "warnings": [],
            }
        )
        cuda_callback = kwargs["cuda_preflight_callback"]
        cuda_callback(
            {
                "available": True,
                "requested_cuda_home": str(kwargs["cuda_home"] or "<not set>"),
                "cuda_home": "/opt/apps/software/CUDA/12.4.0",
                "nvcc": "/opt/apps/software/CUDA/12.4.0/bin/nvcc",
                "source": "module",
                "module": "CUDA/12.4.0",
                "module_default": True,
                "version": "nvcc 12.4",
                "warnings": [],
            }
        )
        build_tool_callback = kwargs["build_tool_preflight_callback"]
        build_tool_callback(
            {
                "available": True,
                "ninja": "/workspace/.anna-deploy-venv/bin/ninja",
                "source": "auto-installed",
                "installed": True,
                "action": "Installed ninja into the workspace deploy environment.",
                "warnings": [],
            }
        )
        callback = kwargs["wait_progress_callback"]
        callback(
            {
                "elapsed": 15,
                "timeout": kwargs["wait_timeout"],
                "pid": 123,
                "base_url": "http://127.0.0.1:8001/v1",
                "last_error": "connection refused",
                "log_tail": "loading with deploy-secret",
            }
        )
        return {
            "command": ["vllm", "serve", "model", "--api-key", "deploy-secret"],
            "cuda_visible_devices": kwargs["gpu"],
            "cuda_home": "/opt/apps/software/CUDA/12.4.0",
            "cuda_module": "CUDA/12.4.0",
            "pid": 123,
            "base_url": "http://127.0.0.1:8001/v1",
        }

    monkeypatch.setattr("anna_agent.cli.deploy_vllm_service", fake_deploy)

    result = runner.invoke(
        app,
        [
            "models",
            "deploy",
            "--workspace",
            str(workspace),
            "--target",
            "complaint",
            "--wait-timeout",
            "30",
            "--gpu",
            "1",
            "--gpu-memory-utilization",
            "0.85",
        ],
        input="deploy-secret\n",
    )

    assert result.exit_code == 0, result.output
    assert "GPU Preflight" in result.output
    assert "CUDA_VISIBLE_DEVICES" in result.output
    assert "NVIDIA A100" in result.output
    assert "cap=69632MiB" in result.output
    assert "CUDA Toolkit Preflight" in result.output
    assert "/opt/apps/software/CUDA/12.4.0/bin/nvcc" in result.output
    assert "Will auto-load this CUDA module" in result.output
    assert "Build Tool Preflight" in result.output
    assert "auto-installed" in result.output
    assert "ninja" in result.output
    assert "module load CUDA/12.4.0 && CUDA_VISIBLE_DEVICES=1" in result.output
    assert "CUDA_HOME=/opt/apps/software/CUDA/12.4.0" in result.output
    assert "Waiting for complaint vLLM" in result.output
    assert "elapsed=15s/30s" in result.output
    assert "loading with ***" in result.output
    assert "deploy-secret" not in result.output


def test_models_env_setup_and_status(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    def fake_setup(workspace_path, python="3.12", force=False, uv_command="uv"):
        assert workspace_path == workspace
        assert python == "3.11"
        assert force is True
        assert uv_command == "/opt/uv"
        return {
            "path": str(workspace / ".anna-deploy-venv"),
            "exists": True,
            "python": str(workspace / ".anna-deploy-venv" / "bin" / "python"),
            "python_exists": True,
            "vllm": str(workspace / ".anna-deploy-venv" / "bin" / "vllm"),
            "vllm_exists": True,
            "available": True,
        }

    monkeypatch.setattr("anna_agent.cli.setup_deploy_env", fake_setup)

    result = runner.invoke(
        app,
        [
            "models",
            "env",
            "setup",
            "--workspace",
            str(workspace),
            "--python",
            "3.11",
            "--force",
            "--uv-command",
            "/opt/uv",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Deploy environment ready" in result.output
    assert "available" in result.output

    result = runner.invoke(
        app,
        ["models", "env", "status", "--workspace", str(workspace)],
    )

    assert result.exit_code == 0, result.output
    assert ".anna-deploy-venv" in result.output


def test_chat_state_uses_stage_based_rich_ui(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    state_file = workspace / "prompts" / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "prompt_only",
                "case_id": "case-1",
                "seeker_id": "seeker-1",
                "portrait": {},
                "report": {},
                "previous_conversations": [],
                "prompt": "Act as a seeker.",
            }
        ),
        encoding="utf-8",
    )

    class FakeFrozenPromptSession:
        def __init__(self, state):
            self.state = state
            self.last_turn_context = {
                "emotion": "sadness",
                "complaint_stage": 1,
                "complaint": "family pressure",
                "memory_used": False,
            }

        def chat(self, message: str) -> str:
            assert message == "你好"
            return "我最近有点累。"

    monkeypatch.setattr("anna_agent.cli.FrozenPromptSession", FakeFrozenPromptSession)

    result = runner.invoke(
        app,
        ["chat", "--workspace", str(workspace), "--state", str(state_file)],
        input="你好\nq\n",
    )

    assert result.exit_code == 0, result.output
    assert "AnnaAgent Chat" in result.output
    assert "Stage 1/2" in result.output
    assert "Stage 2/2" in result.output
    assert "Counselor" in result.output
    assert "Seeker" in result.output
    assert "我最近有点累" in result.output
    assert "ChatCompletion" not in result.output


def test_chat_compact_ui_shows_initialization_progress(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output

    class FakeMsPatient:
        def __init__(self, portrait, report, conversations, progress_callback=None):
            self.last_turn_context = {}
            if progress_callback:
                progress_callback("fake", "Preparing compact initialization")

        def chat(self, message: str) -> str:
            return "我最近有点累。"

    monkeypatch.setattr("anna_agent.ms_patient.MsPatient", FakeMsPatient)

    result = runner.invoke(
        app,
        ["chat", "--workspace", str(workspace)],
        input="q\n",
    )

    assert result.exit_code == 0, result.output
    assert "正在运行：Preparing compact initialization" in result.output


def test_chat_debug_ui_shows_internal_state(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    state_file = workspace / "prompts" / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "prompt_only",
                "case_id": "case-1",
                "seeker_id": "seeker-1",
                "portrait": {},
                "report": {},
                "previous_conversations": [],
                "prompt": "Act as a seeker.",
            }
        ),
        encoding="utf-8",
    )

    class FakeFrozenPromptSession:
        def __init__(self, state):
            self.state = state
            self.last_turn_context = {
                "emotion": "sadness",
                "complaint_stage": 1,
                "complaint": "family pressure",
                "memory_used": False,
            }

        def chat(self, message: str) -> str:
            return "我最近有点累。"

    monkeypatch.setattr("anna_agent.cli.FrozenPromptSession", FakeFrozenPromptSession)

    result = runner.invoke(
        app,
        [
            "chat",
            "--workspace",
            str(workspace),
            "--state",
            str(state_file),
            "--debug-ui",
        ],
        input="你好\nq\n",
    )

    assert result.exit_code == 0, result.output
    assert "调试双模式" in result.output
    assert "本轮内部状态" in result.output
    assert "sadness" in result.output


def test_initialize_full_connection_error_is_concise(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["create", str(workspace)])
    assert result.exit_code == 0, result.output
    case_file = workspace / "cases" / "family_stress_case.json"

    class APIConnectionError(Exception):
        pass

    def fake_build_full_state(case_file, progress_callback=None):
        raise APIConnectionError("Connection error.")

    monkeypatch.setattr("anna_agent.cli.build_full_state", fake_build_full_state)

    result = runner.invoke(
        app,
        [
            "init",
            "full",
            str(case_file),
            "--workspace",
            str(workspace),
        ],
    )

    assert result.exit_code == 1
    assert "Model service connection failed" in result.output
    assert "anna models status" in result.output
    assert "Traceback" not in result.output
