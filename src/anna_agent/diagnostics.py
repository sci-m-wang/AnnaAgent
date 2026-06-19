import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import AnnaEngineConfig, load_config
from .model_services import deploy_install_hint, resolve_vllm_command, vllm_available


@dataclass
class DiagnosticCheck:
    name: str
    status: str
    detail: str


def run_doctor(workspace: Path) -> list[DiagnosticCheck]:
    checks = [
        DiagnosticCheck("anna-agent", "ok", f"version {__version__}"),
        DiagnosticCheck(
            "python", "ok", f"{platform.python_version()} on {sys.platform}"
        ),
    ]
    cfg = _load_config(workspace)
    checks.append(
        DiagnosticCheck(
            "configuration",
            "ok" if cfg else "warn",
            "loaded" if cfg else "using defaults",
        )
    )
    checks.append(_import_check("lancedb", "LanceDB vector store"))
    checks.append(_import_check("rich", "Rich console rendering"))
    checks.append(_import_check("typer", "Typer CLI"))
    vllm_command = resolve_vllm_command(workspace)
    has_vllm = vllm_available(vllm_command)
    checks.append(
        DiagnosticCheck(
            "vllm",
            "ok" if has_vllm else "warn",
            f"available for local SFT deployment: {vllm_command}"
            if has_vllm
            else deploy_install_hint(workspace),
        )
    )
    if cfg:
        checks.append(
            DiagnosticCheck(
                "model service",
                "ok" if cfg.api_key and cfg.base_url else "warn",
                f"model={cfg.model_name}, base_url configured={bool(cfg.base_url)}",
            )
        )
        checks.append(
            DiagnosticCheck(
                "embedding service",
                "ok" if cfg.embedding_api_key and cfg.embedding_base_url else "warn",
                (
                    f"model={cfg.embedding_model_name}, "
                    f"key configured={bool(cfg.embedding_api_key)}"
                ),
            )
        )
        checks.append(
            DiagnosticCheck(
                "memory",
                "ok" if cfg.memory_enabled else "skip",
                f"path={cfg.memory_db_path}, table={cfg.memory_table_name}",
            )
        )
    return checks


def _load_config(workspace: Path) -> AnnaEngineConfig | None:
    try:
        return load_config(workspace)
    except FileNotFoundError:
        return AnnaEngineConfig.load(workspace)


def _import_check(module_name: str, detail: str) -> DiagnosticCheck:
    try:
        __import__(module_name)
    except Exception as err:
        return DiagnosticCheck(module_name, "fail", str(err))
    return DiagnosticCheck(module_name, "ok", detail)
