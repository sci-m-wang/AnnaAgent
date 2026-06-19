import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
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
    cuda_home: Path | None = None,
    gpu_memory_utilization: float | None = None,
    max_model_len: int | None = None,
    pull: bool = True,
    background: bool = True,
    dry_run: bool = False,
    wait_timeout: int = 600,
    wait_progress_interval: int = 15,
    wait_progress_callback: Callable[[dict[str, Any]], None] | None = None,
    gpu_preflight_callback: Callable[[dict[str, Any]], None] | None = None,
    cuda_preflight_callback: Callable[[dict[str, Any]], None] | None = None,
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
        "cuda_visible_devices": gpu or os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "cuda_home": str(cuda_home) if cuda_home else os.environ.get("CUDA_HOME", ""),
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
    preflight = run_gpu_preflight(
        gpu=gpu,
        gpu_memory_utilization=(
            gpu_memory_utilization or spec.default_gpu_memory_utilization
        ),
    )
    result["gpu_preflight"] = preflight
    if gpu_preflight_callback:
        gpu_preflight_callback(preflight)
    cuda_preflight = run_cuda_preflight(cuda_home=cuda_home)
    result["cuda_preflight"] = cuda_preflight
    result["cuda_home"] = cuda_preflight.get("cuda_home", "")
    result["cuda_module"] = cuda_preflight.get("module", "")
    if cuda_preflight_callback:
        cuda_preflight_callback(cuda_preflight)
    if background:
        process = _start_background(workspace, target, command, gpu, cuda_preflight)
        result["pid"] = process.pid
        result["log"] = str(_log_file(workspace, target))
        wait_for_openai_service(
            base_url=base_url,
            api_key=resolved_api_key,
            process=process,
            timeout=wait_timeout,
            progress_interval=wait_progress_interval,
            progress_callback=wait_progress_callback,
            log_path=_log_file(workspace, target),
        )
    else:
        env = _build_service_env(gpu, cuda_preflight)
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


def run_cuda_preflight(cuda_home: Path | None = None) -> dict[str, Any]:
    explicit = cuda_home is not None
    requested = str(cuda_home) if cuda_home else ""
    env_cuda_home = os.environ.get("CUDA_HOME", "")
    warnings = []
    candidates = []
    if cuda_home is not None:
        candidates.append((cuda_home, "--cuda-home"))
    elif env_cuda_home:
        candidates.append((Path(env_cuda_home), "CUDA_HOME"))
    nvcc_from_path = shutil.which("nvcc")
    if nvcc_from_path:
        nvcc_path = Path(nvcc_from_path).resolve()
        candidates.append((nvcc_path.parent.parent, "PATH"))
    candidates.extend((path, "auto-discovered") for path in _discover_cuda_roots())
    seen = set()
    for root, source in candidates:
        root = root.expanduser()
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        nvcc = root / "bin" / "nvcc"
        if nvcc.exists():
            return {
                "available": True,
                "requested_cuda_home": requested or "<not set>",
                "cuda_home": str(root),
                "nvcc": str(nvcc),
                "source": source,
                "version": _nvcc_version(nvcc),
                "warnings": warnings,
            }
    module_info = _cuda_module_preflight()
    if module_info:
        module_info["requested_cuda_home"] = requested or "<not set>"
        module_info["warnings"] = warnings
        return module_info
    if explicit:
        raise RuntimeError(
            f"CUDA toolkit not found under --cuda-home {cuda_home}. "
            "Expected bin/nvcc to exist."
        )
    warnings.append(
        "CUDA toolkit was not found in CUDA_HOME, PATH, common CUDA roots, or "
        "the cluster module system. vLLM may still work, but FlashInfer JIT "
        "can fail without nvcc. Pass --cuda-home /path/to/cuda if this cluster "
        "stores CUDA in a custom location."
    )
    return {
        "available": False,
        "requested_cuda_home": requested or "<not set>",
        "cuda_home": env_cuda_home or "<not set>",
        "nvcc": "<not found>",
        "source": "none",
        "version": "",
        "warnings": warnings,
    }


def _cuda_module_preflight() -> dict[str, Any] | None:
    selected = _select_cuda_module(_available_cuda_modules())
    if not selected:
        return None
    loaded = _load_cuda_module_env(selected["name"])
    if not loaded:
        return None
    env = loaded["env"]
    nvcc = Path(loaded["nvcc"])
    cuda_home = env.get("CUDA_HOME") or str(nvcc.parent.parent)
    return {
        "available": True,
        "requested_cuda_home": "<not set>",
        "cuda_home": cuda_home,
        "nvcc": str(nvcc),
        "source": "module",
        "module": selected["name"],
        "module_default": selected["default"],
        "version": _nvcc_version(nvcc),
        "env": env,
        "warnings": [],
    }


def _available_cuda_modules() -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["bash", "-lc", "module avail cuda 2>&1"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return []
    return _parse_cuda_modules(result.stdout + "\n" + result.stderr)


def _parse_cuda_modules(output: str) -> list[dict[str, Any]]:
    clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    pattern = re.compile(
        r"(?P<name>\b(?:cuda(?:[-_a-zA-Z]*)?|cudatoolkit|cudacore)/"
        r"[A-Za-z0-9][A-Za-z0-9._+-]*)"
        r"(?P<marker>\s*(?:\((?:D|default)\)|\[(?:D|default)\]))?",
        re.IGNORECASE,
    )
    modules = []
    seen = set()
    for match in pattern.finditer(clean):
        name = match.group("name")
        if name in seen:
            continue
        seen.add(name)
        marker = (match.group("marker") or "").lower()
        modules.append(
            {
                "name": name,
                "default": "d" in marker or "default" in marker,
            }
        )
    return modules


def _select_cuda_module(modules: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not modules:
        return None
    defaults = [module for module in modules if module.get("default")]
    pool = defaults or modules
    return max(pool, key=lambda module: _cuda_module_sort_key(str(module["name"])))


def _cuda_module_sort_key(name: str) -> tuple[tuple[int, ...], str]:
    return (tuple(int(part) for part in re.findall(r"\d+", name)), name.lower())


def _load_cuda_module_env(module_name: str) -> dict[str, Any] | None:
    dump_env = "import json, os; print(json.dumps(dict(os.environ)))"
    command = (
        f"module load {shlex.quote(module_name)} >/dev/null 2>&1 && "
        f"command -v nvcc && {shlex.quote(sys.executable)} -c "
        f"{shlex.quote(dump_env)}"
    )
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    try:
        env = json.loads("\n".join(lines[1:]))
    except json.JSONDecodeError:
        return None
    env = _filter_cuda_module_env(env)
    return {"nvcc": lines[0].strip(), "env": env}


def _filter_cuda_module_env(env: dict[str, str]) -> dict[str, str]:
    allowed = {
        "PATH",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "CUDA_HOME",
        "CUDA_PATH",
        "CUDATOOLKIT_HOME",
        "CUDNN_HOME",
        "CMAKE_PREFIX_PATH",
        "PKG_CONFIG_PATH",
        "MANPATH",
        "MODULEPATH",
        "LOADEDMODULES",
        "_LMFILES_",
    }
    filtered = {}
    for key, value in env.items():
        upper = key.upper()
        if key in allowed or "CUDA" in upper or upper.startswith(("CUDNN", "NV")):
            filtered[str(key)] = str(value)
    return filtered


def _discover_cuda_roots() -> list[Path]:
    candidates = []
    for base, pattern in [
        (Path("/usr/local"), "cuda*"),
        (Path("/opt"), "cuda*"),
        (Path("/opt/apps/software/CUDA"), "*"),
    ]:
        if base.exists():
            candidates.extend(path for path in base.glob(pattern) if path.is_dir())
    return sorted(candidates, key=_cuda_sort_key, reverse=True)


def _cuda_sort_key(path: Path) -> tuple[int, ...]:
    parts = []
    for chunk in path.name.replace("-", ".").split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
    return tuple(parts)


def _nvcc_version(nvcc: Path) -> str:
    try:
        result = subprocess.run(
            [str(nvcc), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return ""
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def run_gpu_preflight(
    *, gpu: str | None, gpu_memory_utilization: float
) -> dict[str, Any]:
    if not 0 < gpu_memory_utilization <= 1:
        raise RuntimeError(
            "--gpu-memory-utilization must be greater than 0 and at most 1."
        )
    visible_env = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    requested_ids = _parse_gpu_ids(gpu) if gpu else None
    gpus = _query_nvidia_smi()
    if not gpus:
        raise RuntimeError("No NVIDIA GPUs were reported by nvidia-smi.")
    available_ids = {item["index"] for item in gpus}
    warnings = []
    if requested_ids is None:
        env_ids = (
            _parse_gpu_ids(visible_env) if _is_numeric_gpu_list(visible_env) else None
        )
        if env_ids:
            requested_ids = [env_ids[0]]
            warnings.append(
                "No --gpu value was provided; checked the first GPU from "
                f"CUDA_VISIBLE_DEVICES={visible_env}. Pass --gpu to make the "
                "deployment target explicit."
            )
        else:
            first_gpu = min(available_ids)
            requested_ids = [first_gpu]
            warnings.append(
                f"No --gpu value was provided; checked GPU {first_gpu}. "
                "Pass --gpu 0 or --gpu 1 to make the deployment target explicit."
            )
    selected = (
        [item for item in gpus if item["index"] in requested_ids]
        if requested_ids is not None
        else gpus
    )
    if requested_ids is not None:
        missing = [item for item in requested_ids if item not in available_ids]
        if missing:
            raise RuntimeError(
                "Requested GPU id(s) not found by nvidia-smi: "
                f"{', '.join(str(item) for item in missing)}. "
                "Available GPU id(s): "
                f"{', '.join(str(item) for item in sorted(available_ids))}."
            )
    for item in selected:
        cap_mib = int(item["memory_total_mib"] * gpu_memory_utilization)
        item["vllm_cap_mib"] = cap_mib
        if item["memory_free_mib"] < cap_mib:
            raise RuntimeError(
                f"GPU {item['index']} free memory is below the configured vLLM cap: "
                f"free={item['memory_free_mib']}MiB, cap={cap_mib}MiB. "
                "Choose a less busy GPU or lower --gpu-memory-utilization."
            )
        if cap_mib < 16000:
            warnings.append(
                f"GPU {item['index']} vLLM cap is {cap_mib}MiB, which may be "
                "too low for a 7B model. Consider --gpu-memory-utilization 0.85."
            )
    return {
        "requested_gpu": gpu or "<not set>",
        "cuda_visible_devices": gpu or visible_env or "<not set>",
        "gpu_memory_utilization": gpu_memory_utilization,
        "devices": selected,
        "warnings": warnings,
    }


def _parse_gpu_ids(gpu: str | None) -> list[int] | None:
    if not gpu:
        return None
    ids = []
    for item in gpu.split(","):
        item = item.strip()
        if not item:
            continue
        if not item.isdigit():
            raise RuntimeError(f"Invalid --gpu value: {gpu}. Use comma-separated IDs.")
        ids.append(int(item))
    return ids or None


def _is_numeric_gpu_list(gpu: str) -> bool:
    if not gpu:
        return False
    parts = [item.strip() for item in gpu.split(",") if item.strip()]
    return bool(parts) and all(item.isdigit() for item in parts)


def _query_nvidia_smi() -> list[dict[str, Any]]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,memory.used,memory.free",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError as err:
        raise RuntimeError(
            "nvidia-smi is required for GPU preflight checks but was not found."
        ) from err
    except subprocess.CalledProcessError as err:
        detail = err.stderr.strip() or err.stdout.strip() or str(err)
        raise RuntimeError(f"nvidia-smi failed: {detail}") from err
    gpus = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            continue
        index, name, total, used, free = parts
        gpus.append(
            {
                "index": int(index),
                "name": name,
                "memory_total_mib": int(total),
                "memory_used_mib": int(used),
                "memory_free_mib": int(free),
            }
        )
    return gpus


def wait_for_openai_service(
    *,
    base_url: str,
    api_key: str,
    process: subprocess.Popen[Any] | None = None,
    timeout: int = 600,
    interval: float = 2.0,
    progress_interval: int = 15,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    log_path: Path | None = None,
) -> None:
    start = time.monotonic()
    deadline = start + timeout
    next_progress = start
    last_error = "service did not respond"
    models_url = f"{base_url.rstrip('/')}/models"
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(
                _service_failure_message(
                    f"vLLM process exited with code {process.returncode}",
                    log_path,
                )
            )
        try:
            request = urllib.request.Request(
                models_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                if 200 <= response.status < 300:
                    return
                last_error = f"HTTP {response.status} from {models_url}"
        except Exception as err:
            if isinstance(err, urllib.error.HTTPError):
                last_error = f"HTTP {err.code} from {models_url}"
            else:
                last_error = str(err)
        now = time.monotonic()
        if progress_callback and now >= next_progress:
            progress_callback(
                {
                    "elapsed": int(now - start),
                    "timeout": timeout,
                    "base_url": base_url,
                    "models_url": models_url,
                    "last_error": last_error,
                    "log_path": str(log_path) if log_path else "",
                    "log_tail": _read_log_tail(log_path) if log_path else "",
                    "pid": process.pid if process is not None else None,
                }
            )
            next_progress = now + progress_interval
        time.sleep(interval)
    detail = (
        f"vLLM service was not ready after {timeout}s at {models_url}. "
        f"Last error: {last_error}"
    )
    raise RuntimeError(_service_failure_message(detail, log_path))


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


def _service_failure_message(detail: str, log_path: Path | None) -> str:
    message = detail
    if log_path:
        message += f"\nLog file: {log_path}"
        context = _extract_vllm_failure_context(log_path)
        if context:
            message += f"\nContext before final vLLM engine error:\n{context}"
        tail = _read_log_tail(log_path)
        if tail:
            message += f"\nLast log lines:\n{tail}"
    return message


def _extract_vllm_failure_context(path: Path, before: int = 160) -> str:
    lines = _read_log_lines(path)
    if not lines:
        return ""
    marker_index = None
    for index, line in enumerate(lines):
        has_engine_failure = "Engine core initialization failed" in line
        if has_engine_failure or "See root cause above" in line:
            marker_index = index
    if marker_index is None:
        return ""
    start = max(0, marker_index - before)
    return "\n".join(lines[start : marker_index + 1])


def _read_log_tail(path: Path, lines: int = 40) -> str:
    return "\n".join(_read_log_lines(path)[-lines:])


def _read_log_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8", errors="replace")
    return content.splitlines()


def _start_background(
    workspace: Path,
    target: str,
    command: list[str],
    gpu: str | None,
    cuda_preflight: dict[str, Any] | None = None,
) -> subprocess.Popen[Any]:
    log_path = _log_file(workspace, target)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = _build_service_env(gpu, cuda_preflight)
    log_file = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command, stdout=log_file, stderr=subprocess.STDOUT, env=env
    )
    pid_path = _pid_file(workspace, target)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(process.pid), encoding="utf-8")
    return process


def _build_service_env(
    gpu: str | None, cuda_preflight: dict[str, Any] | None = None
) -> dict[str, str]:
    env = os.environ.copy()
    if cuda_preflight and cuda_preflight.get("available"):
        module_env = cuda_preflight.get("env")
        if isinstance(module_env, dict):
            env.update({str(key): str(value) for key, value in module_env.items()})
        cuda_home = str(cuda_preflight.get("cuda_home", ""))
        if cuda_home:
            env["CUDA_HOME"] = cuda_home
            env["PATH"] = _prepend_env_path(env.get("PATH", ""), f"{cuda_home}/bin")
            lib64 = Path(cuda_home) / "lib64"
            if lib64.exists():
                env["LD_LIBRARY_PATH"] = _prepend_env_path(
                    env.get("LD_LIBRARY_PATH", ""), str(lib64)
                )
    if gpu:
        env["CUDA_VISIBLE_DEVICES"] = gpu
    return env


def _prepend_env_path(current: str, value: str) -> str:
    parts = [part for part in current.split(os.pathsep) if part]
    if value in parts:
        parts.remove(value)
    return os.pathsep.join([value, *parts])


def _pid_file(workspace: Path, target: str) -> Path:
    return workspace / "runs" / "services" / f"{target}.pid"


def _log_file(workspace: Path, target: str) -> Path:
    return workspace / "logs" / "services" / f"{target}.log"
