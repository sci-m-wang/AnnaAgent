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

    result = runner.invoke(app, ["init", str(workspace)])
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
        ["initialize", "prompt-only", str(case_file), "--out", str(state_file)],
    )
    assert result.exit_code == 0, result.output
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


def test_assets_pull_reports_unconfigured_assets(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["init", str(workspace)])
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
        ["assets", "pull", "local-test", "--workspace", str(workspace)],
    )

    assert result.exit_code == 0, result.output
    assert "unconfigured" in result.output


def test_config_secrets_writes_hidden_values_to_dotenv(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = runner.invoke(app, ["init", str(workspace)])
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
