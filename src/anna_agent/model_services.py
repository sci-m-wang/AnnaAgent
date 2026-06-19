import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .assets import find_asset, pull_assets, resolve_asset_target
from .workspace import load_settings, update_env_values, write_settings

WORKSPACE_DEPLOY_ENV_DIR = ".anna-deploy-venv"
DEPLOY_PACKAGE_SPEC = (
    "anna-agent[deploy] @ git+https://github.com/sci-m-wang/AnnaAgent.git"
)


@dataclass(frozen=True)
class SFTServiceSpec:
    name: str
    settings_key: str
    asset_name: str
    asset_path: str
    default_model_name: str
    default_api_key: str
    default_port: int
    default_gpu_memory_utilization: float
    default_max_model_len: int | None = None


SFT_SERVICE_SPECS = {
    "complaint": SFTServiceSpec(
        name="complaint",
        settings_key="complaint",
        asset_name="complaint-sft",
        asset_path="assets/models/complaint-sft",
        default_model_name="complaint",
        default_api_key="complaint_chain",
        default_port=8001,
        default_gpu_memory_utilization=0.3,
        default_max_model_len=1024,
    ),
    "emotion": SFTServiceSpec(
        name="emotion",
        settings_key="emotion",
        asset_name="emotion-sft",
        asset_path="assets/models/emotion-sft",
        default_model_name="emotion",
        default_api_key="emotion_inferencer",
        default_port=8000,
        default_gpu_memory_utilization=0.5,
    ),
}


def expand_targets(target: str) -> list[str]:
    if target == "all":
        return list(SFT_SERVICE_SPECS)
    if target not in SFT_SERVICE_SPECS:
        raise ValueError("target must be one of: complaint, emotion, all")
    return [target]


def set_sft_mode(workspace: Path, target: str, use_sft: bool) -> list[str]:
    settings = load_settings(workspace)
    servers = settings.setdefault("servers", {})
    changed = []
    for name in expand_targets(target):
        spec = SFT_SERVICE_SPECS[name]
        server = servers.setdefault(spec.settings_key, {})
        server["use_sft_model"] = use_sft
        changed.append(name)
    write_settings(workspace, settings)
    return changed


def configure_sft_endpoint(
    workspace: Path,
    *,
    target: str,
    base_url: str,
    model_name: str,
    api_key: str | None = None,
    use_sft: bool = True,
) -> list[str]:
    settings = load_settings(workspace)
    servers = settings.setdefault("servers", {})
    env_updates: dict[str, str] = {}
    changed = []
    for name in expand_targets(target):
        spec = SFT_SERVICE_SPECS[name]
        server = servers.setdefault(spec.settings_key, {})
        server["use_sft_model"] = use_sft
        server["base_url"] = base_url
        server["model_name"] = model_name
        if api_key:
            server["api_key"] = spec.default_api_key
            env_updates[_api_key_env_name(name)] = api_key
        changed.append(name)
    write_settings(workspace, settings)
    if env_updates:
        update_env_values(workspace, env_updates)
    return changed


def vllm_available(vllm_command: str = "vllm") -> bool:
    command = shlex.split(vllm_command)
    if not command:
        return False
    executable = command[0]
    if Path(executable).is_absolute():
        return Path(executable).exists()
    return shutil.which(executable) is not None


def deploy_install_hint(workspace: Path) -> str:
    return (
        "vLLM is not available for this workspace. Run "
        f"`anna models env setup --workspace {workspace}` to create "
        f"{WORKSPACE_DEPLOY_ENV_DIR}, or run "
        f"`anna init {workspace} --deploy-env` when initializing a new "
        "workspace. Alternatively, pass --vllm-command /path/to/vllm, or use "
        "`anna models configure` with an existing OpenAI-compatible endpoint."
    )


def deploy_env_path(workspace: Path) -> Path:
    return workspace / WORKSPACE_DEPLOY_ENV_DIR


def deploy_env_python_path(workspace: Path) -> Path:
    if os.name == "nt":
        return deploy_env_path(workspace) / "Scripts" / "python.exe"
    return deploy_env_path(workspace) / "bin" / "python"


def deploy_env_vllm_path(workspace: Path) -> Path:
    if os.name == "nt":
        return deploy_env_path(workspace) / "Scripts" / "vllm.exe"
    return deploy_env_path(workspace) / "bin" / "vllm"


def deploy_env_status(workspace: Path) -> dict[str, Any]:
    env_path = deploy_env_path(workspace)
    python_path = deploy_env_python_path(workspace)
    vllm_path = deploy_env_vllm_path(workspace)
    return {
        "path": str(env_path),
        "exists": env_path.exists(),
        "python": str(python_path),
        "python_exists": python_path.exists(),
        "vllm": str(vllm_path),
        "vllm_exists": vllm_path.exists(),
        "available": vllm_available(str(vllm_path)),
    }


def resolve_vllm_command(workspace: Path, vllm_command: str = "vllm") -> str:
    if vllm_command != "vllm":
        return vllm_command
    workspace_vllm = deploy_env_vllm_path(workspace)
    if vllm_available(str(workspace_vllm)):
        return str(workspace_vllm)
    return vllm_command


def setup_deploy_env(
    workspace: Path,
    *,
    python: str = "3.12",
    force: bool = False,
    uv_command: str = "uv",
    package_spec: str = DEPLOY_PACKAGE_SPEC,
) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    env_path = deploy_env_path(workspace)
    python_path = deploy_env_python_path(workspace)
    uv_executable = _resolve_executable(uv_command)
    if force and env_path.exists():
        shutil.rmtree(env_path)
    if not python_path.exists():
        _run_checked(
            [uv_executable, "venv", "--python", python, str(env_path)],
            "create workspace deploy environment",
        )
    _run_checked(
        [uv_executable, "pip", "install", "--python", str(python_path), package_spec],
        "install AnnaAgent deploy dependencies",
    )
    status = deploy_env_status(workspace)
    status["package_spec"] = package_spec
    return status


def build_vllm_command(
    *,
    vllm_command: str = "vllm",
    model_path: Path,
    host: str,
    port: int,
    api_key: str,
    model_name: str,
    gpu_memory_utilization: float,
    max_model_len: int | None,
    extra_args: list[str] | None = None,
) -> list[str]:
    command = shlex.split(vllm_command) + [
        "serve",
        str(model_path),
        "--host",
        host,
        "--port",
        str(port),
        "--dtype",
        "auto",
        "--api-key",
        api_key,
        "--served-model-name",
        model_name,
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        "hermes",
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
    ]
    if max_model_len:
        command.extend(["--max-model-len", str(max_model_len)])
    if extra_args:
        command.extend(extra_args)
    return command


def deploy_vllm_service(
    workspace: Path,
    *,
    target: str,
    model_path: Path | None = None,
    manifest_file: Path | None = None,
    vllm_command: str = "vllm",
    host: str = "127.0.0.1",
    public_host: str = "127.0.0.1",
    port: int | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    gpu: str | None = None,
    gpu_memory_utilization: float | None = None,
    max_model_len: int | None = None,
    pull: bool = True,
    background: bool = True,
    dry_run: bool = False,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    load_settings(workspace)
    spec = SFT_SERVICE_SPECS[target]
    resolved_model_path = _resolve_model_path(
        workspace, spec, model_path, manifest_file=manifest_file
    )
    if (
        pull
        and not dry_run
        and model_path is None
        and not _has_files(resolved_model_path)
    ):
        pull_assets(
            workspace,
            [spec.asset_name],
            force=False,
            manifest_file=manifest_file,
        )
    if not _has_files(resolved_model_path) and not dry_run:
        raise FileNotFoundError(
            f"Model files not found at {resolved_model_path}. "
            "Run `anna assets pull paper` or pass --model-path."
        )
    resolved_port = port or spec.default_port
    resolved_api_key = api_key or spec.default_api_key
    resolved_model_name = model_name or spec.default_model_name
    resolved_max_model_len = (
        max_model_len if max_model_len is not None else spec.default_max_model_len
    )
    resolved_vllm_command = resolve_vllm_command(workspace, vllm_command)
    command = build_vllm_command(
        vllm_command=resolved_vllm_command,
        model_path=resolved_model_path,
        host=host,
        port=resolved_port,
        api_key=resolved_api_key,
        model_name=resolved_model_name,
        gpu_memory_utilization=(
            gpu_memory_utilization or spec.default_gpu_memory_utilization
        ),
        max_model_len=resolved_max_model_len,
        extra_args=extra_args,
    )
    base_url = f"http://{public_host}:{resolved_port}/v1"
    result: dict[str, Any] = {
        "target": target,
        "command": command,
        "base_url": base_url,
        "model_name": resolved_model_name,
        "api_key": resolved_api_key,
        "model_path": str(resolved_model_path),
        "pid": None,
    }
    if dry_run:
        return result
    if not vllm_available(resolved_vllm_command):
        raise RuntimeError(deploy_install_hint(workspace))
    if background:
        pid = _start_background(workspace, target, command, gpu)
        result["pid"] = pid
    else:
        env = os.environ.copy()
        if gpu:
            env["CUDA_VISIBLE_DEVICES"] = gpu
        subprocess.run(command, check=True, env=env)
    configure_sft_endpoint(
        workspace,
        target=target,
        base_url=base_url,
        model_name=resolved_model_name,
        api_key=resolved_api_key,
        use_sft=True,
    )
    return result


def service_status(workspace: Path) -> list[dict[str, Any]]:
    settings = load_settings(workspace)
    servers = settings.get("servers", {})
    statuses = []
    for name, spec in SFT_SERVICE_SPECS.items():
        server = servers.get(spec.settings_key, {})
        pid_file = _pid_file(workspace, name)
        pid = pid_file.read_text(encoding="utf-8").strip() if pid_file.exists() else ""
        statuses.append(
            {
                "target": name,
                "use_sft": bool(server.get("use_sft_model")),
                "base_url": server.get("base_url", ""),
                "model_name": server.get("model_name", ""),
                "pid": pid,
                "log": str(_log_file(workspace, name)),
            }
        )
    return statuses


def _resolve_model_path(
    workspace: Path,
    spec: SFTServiceSpec,
    model_path: Path | None,
    manifest_file: Path | None = None,
) -> Path:
    if model_path is not None:
        return model_path if model_path.is_absolute() else workspace / model_path
    asset = find_asset(workspace, spec.asset_name, manifest_file=manifest_file)
    if asset:
        return resolve_asset_target(workspace, asset, manifest_file=manifest_file)
    return workspace / spec.asset_path


def _has_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def _resolve_executable(command: str) -> str:
    parts = shlex.split(command)
    if len(parts) != 1:
        raise ValueError("uv command must be a single executable path or name")
    executable = parts[0]
    if Path(executable).is_absolute():
        if Path(executable).exists():
            return executable
        raise FileNotFoundError(f"Executable not found: {executable}")
    resolved = shutil.which(executable)
    if not resolved:
        raise FileNotFoundError(
            "uv is required to create the workspace deploy environment. "
            "Install uv or pass --uv-command /path/to/uv."
        )
    return resolved


def _run_checked(command: list[str], action: str) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f"Failed to {action}: {err}") from err


def _api_key_env_name(target: str) -> str:
    return f"ANNA_ENGINE_{target.upper()}_API_KEY"


def _start_background(
    workspace: Path, target: str, command: list[str], gpu: str | None
) -> int:
    log_path = _log_file(workspace, target)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if gpu:
        env["CUDA_VISIBLE_DEVICES"] = gpu
    log_file = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command, stdout=log_file, stderr=subprocess.STDOUT, env=env
    )
    pid_path = _pid_file(workspace, target)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(process.pid), encoding="utf-8")
    return process.pid


def _pid_file(workspace: Path, target: str) -> Path:
    return workspace / "runs" / "services" / f"{target}.pid"


def _log_file(workspace: Path, target: str) -> Path:
    return workspace / "logs" / "services" / f"{target}.log"
