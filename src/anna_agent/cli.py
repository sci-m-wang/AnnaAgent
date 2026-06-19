import json
import logging
import shutil
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from . import __version__, backbone
from .assets import list_assets, manifest_path, pull_assets, resolve_asset_target
from .case_data import (
    discover_case_files,
    get_interactive_config_path,
    load_case,
    load_document,
    load_seeker_data,
    sample_case,
    validate_case,
    write_case_json,
)
from .common.registry import registry
from .diagnostics import run_doctor
from .memory import LanceMemoryStore
from .model_services import (
    configure_sft_endpoint,
    deploy_env_status,
    deploy_vllm_service,
    expand_targets,
    service_status,
    set_sft_mode,
    setup_deploy_env,
)
from .runtime import (
    FrozenPromptSession,
    append_jsonl,
    build_full_state,
    build_prompt_only_state,
    load_script_messages,
    load_state,
    save_state,
    state_summary,
)
from .workspace import (
    initialize_workspace,
    load_settings,
    redact_config,
    set_config_value,
    update_env_values,
    write_settings,
)

console = Console()

app = typer.Typer(help="AnnaAgent CLI", invoke_without_command=True)
assets_app = typer.Typer(help="Download and inspect experiment assets")
config_app = typer.Typer(help="Configure AnnaAgent workspaces")
test_app = typer.Typer(help="Run connectivity and smoke tests")
data_app = typer.Typer(help="Validate and prepare case data")
memory_app = typer.Typer(help="Manage LanceDB long-term memory")
initialize_app = typer.Typer(help="Create or inspect initialization states")
models_app = typer.Typer(help="Configure or deploy SFT model services")
models_env_app = typer.Typer(help="Manage workspace deploy environments")
run_app = typer.Typer(help="Run batch experiments")
logs_app = typer.Typer(help="Inspect local run logs")
cache_app = typer.Typer(help="Inspect or clean local caches")
reset_app = typer.Typer(help="Reset workspace artifacts")

app.add_typer(assets_app, name="assets")
app.add_typer(config_app, name="config")
app.add_typer(test_app, name="test")
app.add_typer(data_app, name="data")
app.add_typer(memory_app, name="memory")
app.add_typer(initialize_app, name="initialize")
app.add_typer(models_app, name="models")
models_app.add_typer(models_env_app, name="env")
app.add_typer(run_app, name="run")
app.add_typer(logs_app, name="logs")
app.add_typer(cache_app, name="cache")
app.add_typer(reset_app, name="reset")


def _get_config_path(root: Path) -> Path:
    return get_interactive_config_path(root)


def _load_seeker_data(config_path: Path) -> tuple[dict, dict, list]:
    return load_seeker_data(config_path)


def _configure(workspace: Path) -> None:
    backbone.configure(workspace)


def _resolve_path(workspace: Path, value: Path) -> Path:
    return value if value.is_absolute() else workspace / value


def _resolve_seeker_id(workspace: Path, seeker_id: str | None) -> str:
    if seeker_id:
        return seeker_id
    cfg_path = _get_config_path(workspace)
    portrait, _, _ = _load_seeker_data(cfg_path)
    return portrait.get("_seeker_id", "default-case")


@contextmanager
def _suppress_stdio(enabled: bool):
    if not enabled:
        yield
        return
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        yield


def _configure_chat_logging(debug_ui: bool) -> None:
    level = logging.DEBUG if debug_ui else logging.WARNING
    logging.getLogger("anna_agent").setLevel(level)


def _render_chat_header(debug_ui: bool) -> None:
    mode = "调试双模式" if debug_ui else "默认清爽模式"
    console.print(
        Panel.fit(
            "[bold cyan]AnnaAgent Chat[/bold cyan]\n"
            f"[dim]模式：{mode}。输入 exit / quit / q 结束会话。[/dim]",
            border_style="cyan",
        )
    )


def _render_config_summary(
    *, workspace: Path, source: Path | None, source_kind: str, debug_ui: bool
) -> None:
    cfg = registry.get("anna_engine_config")
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Workspace", str(workspace))
    if source:
        table.add_row(source_kind, str(source))
    table.add_row("Base model", cfg.model_name)
    table.add_row("Base endpoint", cfg.base_url)
    table.add_row("Memory", "on" if cfg.memory_enabled else "off")
    table.add_row("Debug UI", "on" if debug_ui else "off")
    console.print(Panel(table, title="配置摘要", border_style="blue"))


def _render_initialization_events(events: list[tuple[str, str]]) -> None:
    if not events:
        return
    table = Table(title="初始化流程", show_lines=False)
    table.add_column("Step", style="bold magenta")
    table.add_column("Status")
    for stage, detail in events:
        table.add_row(stage, detail)
    console.print(table)


def _render_debug_context(seeker: Any) -> None:
    context = getattr(seeker, "last_turn_context", None)
    if not context:
        return
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold magenta")
    table.add_column("Value")
    for key in ["emotion", "complaint_stage", "complaint", "memory_used"]:
        if key in context:
            table.add_row(key, str(context[key]))
    console.print(Panel(table, title="本轮内部状态", border_style="magenta"))


def _print_deploy_env_status(status: dict[str, Any]) -> None:
    table = Table(title="Workspace Deploy Environment")
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    for key in [
        "path",
        "exists",
        "python",
        "python_exists",
        "vllm",
        "vllm_exists",
        "available",
    ]:
        table.add_row(key, str(status.get(key, "")))
    console.print(table)


def _looks_like_connection_error(err: BaseException) -> bool:
    current: BaseException | None = err
    while current is not None:
        if current.__class__.__name__ in {"APIConnectionError", "ConnectError"}:
            return True
        current = current.__cause__ or current.__context__
    return False


def _print_model_connection_help(workspace: Path, err: BaseException) -> None:
    console.print(f"[red]Model service connection failed:[/red] {escape(str(err))}")
    console.print(
        "Run [bold]anna doctor --workspace {workspace}[/bold] and "
        "[bold]anna models status --workspace {workspace}[/bold]. If you use "
        "local SFT models, rerun [bold]anna models deploy --wait-timeout 900 "
        "--workspace {workspace}[/bold] and inspect logs/services/*.log."
        .format(workspace=workspace)
    )


def _print_deploy_wait_progress(
    target: str, info: dict[str, Any], secrets: list[str]
) -> None:
    elapsed = info.get("elapsed", 0)
    timeout = info.get("timeout", 0)
    pid = info.get("pid") or "?"
    last_error = _redact_text(str(info.get("last_error", "")), secrets)
    console.print(
        f"[yellow]Waiting for {target} vLLM[/yellow] "
        f"elapsed={elapsed}s/{timeout}s pid={pid} "
        f"endpoint={escape(str(info.get('base_url', '')))} "
        f"last_error={escape(last_error)}"
    )
    log_tail = _redact_text(str(info.get("log_tail", "")), secrets).strip()
    if log_tail:
        console.print(
            Panel(
                escape(log_tail),
                title=f"{target} logs/services tail",
                border_style="yellow",
            )
        )


def _print_gpu_preflight(target: str, info: dict[str, Any]) -> None:
    table = Table(title=f"GPU Preflight · {target}")
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", overflow="fold")
    table.add_row("requested_gpu", str(info.get("requested_gpu", "")))
    table.add_row("CUDA_VISIBLE_DEVICES", str(info.get("cuda_visible_devices", "")))
    table.add_row("gpu_memory_utilization", str(info.get("gpu_memory_utilization", "")))
    for device in info.get("devices", []):
        table.add_row(
            f"GPU {device.get('index')}",
            (
                f"{device.get('name')} | "
                f"total={device.get('memory_total_mib')}MiB "
                f"free={device.get('memory_free_mib')}MiB "
                f"vLLM cap={device.get('vllm_cap_mib')}MiB"
            ),
        )
    for warning in info.get("warnings", []):
        table.add_row("warning", f"[yellow]{escape(str(warning))}[/yellow]")
    console.print(table)


def _print_cuda_preflight(target: str, info: dict[str, Any]) -> None:
    table = Table(title=f"CUDA Toolkit Preflight · {target}")
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", overflow="fold")
    table.add_row("available", str(info.get("available", False)))
    table.add_row("requested_cuda_home", str(info.get("requested_cuda_home", "")))
    table.add_row("CUDA_HOME", str(info.get("cuda_home", "")))
    table.add_row("nvcc", str(info.get("nvcc", "")))
    table.add_row("source", str(info.get("source", "")))
    if info.get("version"):
        table.add_row("version", str(info.get("version", "")))
    if info.get("available"):
        table.add_row(
            "action",
            "Will inject CUDA_HOME/PATH/LD_LIBRARY_PATH into the vLLM process.",
        )
    for warning in info.get("warnings", []):
        table.add_row("warning", f"[yellow]{escape(str(warning))}[/yellow]")
    console.print(table)


def _interactive_chat(
    seeker: Any, save: Path | None = None, *, debug_ui: bool = False
) -> None:
    console.print(Rule("[bold green]Stage 2/2 · Chat[/bold green]"))
    console.print(
        Panel(
            "[bold]Counselor[/bold] 输入咨询师发言；[bold green]Seeker[/bold green] "
            "面板显示来访者回复。",
            border_style="green",
        )
    )
    turn = 1
    while True:
        message = console.input("[bold cyan]Counselor[/bold cyan] [dim]›[/dim] ")
        if message.lower() in {"exit", "quit", "q"}:
            break
        console.print(
            Panel(
                escape(message),
                title=f"Counselor · Turn {turn}",
                border_style="cyan",
            )
        )
        try:
            if debug_ui:
                response = seeker.chat(message)
            else:
                with console.status("[green]Seeker 正在生成回复...[/green]"):
                    with _suppress_stdio(True):
                        response = seeker.chat(message)
        except Exception as err:
            console.print(f"[red]Error:[/red] {err}")
            continue
        if isinstance(response, tuple):
            response_text = response[0]
        else:
            response_text = response
        if debug_ui:
            _render_debug_context(seeker)
        console.print(
            Panel(
                escape(response_text or "<empty response>"),
                title="Seeker",
                border_style="green",
            )
        )
        if save:
            append_jsonl(save, {"role": "Counselor", "content": message})
            append_jsonl(save, {"role": "Seeker", "content": response_text})
        turn += 1


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show package version."),
    workspace: Path = typer.Option(
        Path(),
        "--workspace",
        "--root",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        help="Workspace containing settings.yaml and cases.",
    ),
) -> None:
    if version:
        console.print(f"anna-agent {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is not None:
        return
    chat(workspace=workspace, case=None, state=None, save=None, debug_ui=False)


@app.command("doctor")
def doctor(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    table = Table(title="AnnaAgent Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in run_doctor(workspace):
        color = {"ok": "green", "warn": "yellow", "fail": "red", "skip": "cyan"}.get(
            check.status, "white"
        )
        table.add_row(
            escape(check.name),
            f"[{color}]{escape(check.status)}[/{color}]",
            escape(check.detail),
        )
    console.print(table)


@app.command("init")
def init_workspace(
    target: Path = typer.Argument(Path("anna-workspace"), help="Workspace directory."),
    force: bool = typer.Option(False, "--force", help="Overwrite generated files."),
    deploy_env: bool = typer.Option(
        False,
        "--deploy-env",
        help="Also create a workspace vLLM deployment environment.",
    ),
    deploy_python: str = typer.Option(
        "3.12",
        "--deploy-python",
        help="Python version used for the workspace deployment environment.",
    ),
    deploy_force: bool = typer.Option(
        False,
        "--deploy-force",
        help="Recreate the workspace deployment environment if it exists.",
    ),
) -> None:
    initialize_workspace(target, force=force)
    console.print(f"[green]Workspace initialized:[/green] {target}")
    if deploy_env:
        try:
            status = setup_deploy_env(
                target,
                python=deploy_python,
                force=deploy_force,
            )
        except Exception as err:
            console.print(f"[red]Deploy environment setup failed:[/red] {err}")
            raise typer.Exit(code=1) from None
        console.print(
            f"[green]Deploy environment ready:[/green] {status['path']}"
        )
        console.print(f"vLLM command: {status['vllm']}")


@assets_app.command("list")
def assets_list(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help="Path to an asset manifest JSON file.",
        resolve_path=True,
    ),
) -> None:
    table = Table(title=f"Assets manifest: {manifest_path(workspace, manifest)}")
    table.add_column("Name")
    table.add_column("Kind")
    table.add_column("Status")
    table.add_column("Target")
    table.add_column("Resolved Path")
    for asset in list_assets(workspace, manifest_file=manifest):
        source = asset.get("source", {})
        configured = bool(source.get("url")) or bool(source.get("repo_id"))
        table.add_row(
            asset.get("name", ""),
            asset.get("kind", ""),
            "configured" if configured else "unconfigured",
            asset.get("target", ""),
            str(resolve_asset_target(workspace, asset, manifest_file=manifest)),
        )
    console.print(table)


@assets_app.command("pull")
def assets_pull(
    names: list[str] = typer.Argument(None, help="Asset names or preset names."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    force: bool = typer.Option(False, "--force", help="Redownload existing files."),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help="Path to an asset manifest JSON file.",
        resolve_path=True,
    ),
    target: Path | None = typer.Option(
        None,
        "--target",
        help="Override target directory for one explicitly selected asset.",
    ),
) -> None:
    results = pull_assets(
        workspace,
        names or [],
        force=force,
        manifest_file=manifest,
        target_override=target,
    )
    table = Table(title="Asset Pull Results")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Path")
    for result in results:
        table.add_row(result["name"], result["status"], result.get("path", ""))
    console.print(table)


@config_app.command("show")
def config_show(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    redact: bool = typer.Option(True, "--redact/--no-redact"),
) -> None:
    data = load_settings(workspace)
    if redact:
        data = redact_config(data)
    console.print(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Dotted key, e.g. model_service.base_url."),
    value: str = typer.Argument(..., help="YAML-parsed value."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    parsed = yaml.safe_load(value)
    set_config_value(workspace, key, parsed)
    console.print(f"[green]Updated[/green] {key}")


@config_app.command("validate")
def config_validate(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    console.print(f"[green]Configuration valid.[/green] model={cfg.model_name}")


@config_app.command("wizard")
def config_wizard(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    data = load_settings(workspace)
    data.setdefault("model_service", {})["model_name"] = typer.prompt(
        "Base model name", default=data.get("model_service", {}).get("model_name", "")
    )
    data["model_service"]["base_url"] = typer.prompt(
        "Base model base URL", default=data.get("model_service", {}).get("base_url", "")
    )
    data.setdefault("embedding", {})["model_name"] = typer.prompt(
        "Embedding model", default=data.get("embedding", {}).get("model_name", "")
    )
    data["embedding"]["base_url"] = typer.prompt(
        "Embedding base URL", default=data.get("embedding", {}).get("base_url", "")
    )
    write_settings(workspace, data)
    _prompt_and_write_secrets(workspace)
    console.print(
        "[green]Configuration wizard complete.[/green] Secrets were written to .env."
    )


@config_app.command("secrets")
def config_secrets(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    sft: bool = typer.Option(False, "--sft", help="Also prompt for SFT service keys."),
) -> None:
    _prompt_and_write_secrets(workspace, include_sft=sft)
    console.print("[green]Secrets updated in .env.[/green]")


def _prompt_and_write_secrets(workspace: Path, include_sft: bool = False) -> None:
    prompts = [
        ("ANNA_ENGINE_API_KEY", "Base model API key"),
        ("ANNA_ENGINE_EMBEDDING_API_KEY", "Embedding API key"),
    ]
    if include_sft:
        prompts.extend(
            [
                ("ANNA_ENGINE_COMPLAINT_API_KEY", "Complaint SFT API key"),
                ("ANNA_ENGINE_COUNSELOR_API_KEY", "Counselor API key"),
                ("ANNA_ENGINE_EMOTION_API_KEY", "Emotion SFT API key"),
            ]
        )
    updates = {}
    for env_key, label in prompts:
        value = typer.prompt(
            f"{label} (leave blank to keep current)",
            default="",
            hide_input=True,
            show_default=False,
        )
        if value:
            updates[env_key] = value
    if updates:
        update_env_values(workspace, updates)


@test_app.command("embedding")
def test_embedding(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    from .memory.embeddings import OpenAIEmbeddingProvider

    provider = OpenAIEmbeddingProvider(
        api_key=cfg.embedding_api_key or cfg.api_key,
        base_url=cfg.embedding_base_url or cfg.base_url,
        model_name=cfg.embedding_model_name,
    )
    vector = provider.embed_texts(["AnnaAgent embedding connectivity test"])[0]
    console.print(f"[green]Embedding OK[/green] dimension={len(vector)}")


@test_app.command("model")
def test_model(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    client = backbone.get_openai_client()
    response = client.chat.completions.create(
        model=cfg.model_name,
        messages=[{"role": "user", "content": "Reply with OK."}],
    )
    console.print(
        f"[green]Model OK[/green] response={response.choices[0].message.content}"
    )


@test_app.command("memory")
def test_memory(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    case = sample_case()
    count = store.index_case(
        seeker_id=case["id"],
        case_id=case["id"],
        portrait=case["portrait"],
        report=case["report"],
        conversations=case["conversation"],
        window_size=cfg.memory_window_size,
        window_stride=cfg.memory_window_stride,
    )
    hits = store.search("家庭压力和胸闷", seeker_id=case["id"], top_k=3)
    console.print(f"[green]Memory OK[/green] indexed={count}, hits={len(hits)}")


@test_app.command("all")
def test_all(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    doctor(workspace)
    test_embedding(workspace)
    test_memory(workspace)


@data_app.command("validate")
def data_validate(files: list[Path] = typer.Argument(..., help="Case files.")) -> None:
    failed = False
    for file in files:
        errors = validate_case(load_document(file))
        if errors:
            failed = True
            console.print(f"[red]{file}[/red]")
            for error in errors:
                console.print(f"  - {error}")
        else:
            console.print(f"[green]OK[/green] {file}")
    if failed:
        raise typer.Exit(code=1)


@data_app.command("inspect")
def data_inspect(file: Path = typer.Argument(..., help="Case file.")) -> None:
    case = load_case(file)
    table = Table(title=str(file))
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("case_id", case["id"])
    table.add_row("seeker_id", case["seeker_id"])
    table.add_row("turns", str(len(case["conversation"])))
    table.add_row("report_sections", str(len(case["report"])))
    table.add_row("symptoms", str(case["portrait"].get("symptoms", "")))
    console.print(table)


@data_app.command("convert")
def data_convert(
    source: Path = typer.Argument(...),
    output: Path = typer.Option(..., "--out", "-o"),
) -> None:
    case = load_case(source)
    write_case_json(case, output)
    console.print(f"[green]Wrote[/green] {output}")


@data_app.command("sample")
def data_sample(
    output: Path = typer.Option(Path("cases/family_stress_case.json"), "--out", "-o"),
) -> None:
    write_case_json(sample_case(), output)
    console.print(f"[green]Wrote sample case[/green] {output}")


@memory_app.command("index")
def memory_index(
    case_file: Path = typer.Argument(
        ..., help="Path to an interactive JSON/YAML case file."
    ),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    seeker_id: str | None = typer.Option(
        None, help="Override the seeker id used for filtering."
    ),
    session_id: str = typer.Option("session-001", help="Session id for this case."),
    session_index: int = typer.Option(1, help="Session order for this case."),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    case = load_case(case_file)
    resolved_seeker_id = seeker_id or case["seeker_id"]
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    count = store.index_case(
        seeker_id=resolved_seeker_id,
        case_id=case["id"],
        portrait=case["portrait"],
        report=case["report"],
        conversations=case["conversation"],
        session_id=session_id,
        session_index=session_index,
        window_size=cfg.memory_window_size,
        window_stride=cfg.memory_window_stride,
    )
    console.print(
        f"[green]Indexed {count} new memory chunks[/green] for {resolved_seeker_id}."
    )


@memory_app.command("search")
def memory_search(
    query_text: str = typer.Argument(..., help="Query text for long-term memory."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    seeker_id: str | None = typer.Option(
        None, help="Defaults to the current interactive file id."
    ),
    top_k: int | None = typer.Option(None, help="Number of chunks to show."),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    resolved_seeker_id = _resolve_seeker_id(workspace, seeker_id)
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    hits = store.search(
        query_text, seeker_id=resolved_seeker_id, top_k=top_k or cfg.memory_top_k
    )
    _print_hits(hits, resolved_seeker_id)


@memory_app.command("stats")
def memory_stats(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    table_obj = store._open_table()
    count = table_obj.count_rows() if table_obj is not None else 0
    console.print(f"chunks={count}, db={store.db_path}, table={store.table_name}")


@memory_app.command("inspect")
def memory_inspect(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    path = store.db_path.parent / "sessions.json"
    if not path.exists():
        console.print("[yellow]No session metadata found.[/yellow]")
        return
    console.print(path.read_text(encoding="utf-8"))


@memory_app.command("reset")
def memory_reset(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    yes: bool = typer.Option(False, "--yes", help="Do not prompt."),
) -> None:
    _configure(workspace)
    cfg = registry.get("anna_engine_config")
    store = LanceMemoryStore.from_config(cfg, workspace=workspace)
    if not yes and not typer.confirm(f"Delete {store.db_path.parent}?", default=False):
        raise typer.Exit()
    shutil.rmtree(store.db_path.parent, ignore_errors=True)
    console.print("[green]Memory reset complete.[/green]")


@initialize_app.command("prompt-only")
def initialize_prompt_only(
    case_file: Path = typer.Argument(..., help="Case file."),
    output: Path = typer.Option(Path("prompts/prompt_state.json"), "--out", "-o"),
) -> None:
    state = build_prompt_only_state(case_file)
    save_state(state, output)
    console.print(f"[green]Wrote prompt-only state[/green] {output}")


@initialize_app.command("full")
def initialize_full(
    case_file: Path = typer.Argument(..., help="Case file."),
    output: Path = typer.Option(Path("prompts/full_state.json"), "--out", "-o"),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    try:
        state = build_full_state(case_file)
    except Exception as err:
        if _looks_like_connection_error(err):
            _print_model_connection_help(workspace, err)
            raise typer.Exit(code=1) from None
        raise
    save_state(state, output)
    console.print(f"[green]Wrote full state[/green] {output}")


@initialize_app.command("freeze")
def initialize_freeze(
    case_file: Path = typer.Argument(..., help="Case file."),
    output: Path = typer.Option(Path("prompts/frozen_state.json"), "--out", "-o"),
    mode: str = typer.Option("full", help="full or prompt-only."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    if mode == "prompt-only":
        initialize_prompt_only(case_file, output)
        return
    initialize_full(case_file, output, workspace)


@initialize_app.command("from-prompt")
def initialize_from_prompt(
    state_file: Path = typer.Argument(..., help="Frozen state JSON."),
) -> None:
    state = load_state(state_file)
    console.print(json.dumps(state_summary(state), ensure_ascii=False, indent=2))


@models_app.command("use-base")
def models_use_base(
    target: str = typer.Option("all", help="complaint, emotion, or all."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    changed = set_sft_mode(workspace, target=target, use_sft=False)
    console.print(f"[green]Using base model for:[/green] {', '.join(changed)}")
    console.print(
        f"Run [bold]anna test model --workspace {workspace}[/bold] before chat."
    )


@models_app.command("use-sft")
def models_use_sft(
    target: str = typer.Option("all", help="complaint, emotion, or all."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    changed = set_sft_mode(workspace, target=target, use_sft=True)
    console.print(f"[green]Using SFT model for:[/green] {', '.join(changed)}")


@models_app.command("configure")
def models_configure(
    target: str = typer.Option(..., help="complaint, emotion, or all."),
    base_url: str = typer.Option(..., help="OpenAI-compatible endpoint /v1 URL."),
    model_name: str = typer.Option(..., help="Served model name."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    api_key: str | None = typer.Option(
        None, help="API key. Prompts hidden if omitted."
    ),
    use_sft: bool = typer.Option(True, "--use-sft/--no-use-sft"),
) -> None:
    secret = api_key
    if secret is None:
        secret = typer.prompt(
            "SFT endpoint API key (leave blank to keep current)",
            default="",
            hide_input=True,
            show_default=False,
        )
    changed = configure_sft_endpoint(
        workspace,
        target=target,
        base_url=base_url,
        model_name=model_name,
        api_key=secret or None,
        use_sft=use_sft,
    )
    console.print(f"[green]Configured SFT endpoint for:[/green] {', '.join(changed)}")


@models_env_app.command("setup")
def models_env_setup(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    python: str = typer.Option(
        "3.12",
        "--python",
        help="Python version used for the workspace deployment environment.",
    ),
    force: bool = typer.Option(
        False, "--force", help="Recreate the workspace deployment environment."
    ),
    uv_command: str = typer.Option(
        "uv", "--uv-command", help="uv executable path or name."
    ),
) -> None:
    try:
        status = setup_deploy_env(
            workspace,
            python=python,
            force=force,
            uv_command=uv_command,
        )
    except Exception as err:
        console.print(f"[red]Deploy environment setup failed:[/red] {err}")
        raise typer.Exit(code=1) from None
    console.print(f"[green]Deploy environment ready:[/green] {status['path']}")
    _print_deploy_env_status(status)


@models_env_app.command("status")
def models_env_status(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _print_deploy_env_status(deploy_env_status(workspace))


@models_app.command("deploy")
def models_deploy(
    target: str = typer.Option(..., help="complaint, emotion, or all."),
    backend: str = typer.Option("vllm", help="Deployment backend. Currently: vllm."),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help="Path to an asset manifest JSON file.",
        resolve_path=True,
    ),
    model_path: Path | None = typer.Option(
        None, help="Local model path. Defaults to asset path."
    ),
    vllm_command: str = typer.Option(
        "vllm",
        "--vllm-command",
        help="vLLM executable or command prefix, e.g. /path/to/vllm.",
    ),
    host: str = typer.Option("127.0.0.1", help="vLLM bind host."),
    public_host: str = typer.Option("127.0.0.1", help="Host written to settings.yaml."),
    port: int | None = typer.Option(None, help="Service port. Defaults by target."),
    api_key: str | None = typer.Option(None, help="API key for vLLM service."),
    model_name: str | None = typer.Option(None, help="Served model name."),
    gpu: str | None = typer.Option(
        None, help="CUDA_VISIBLE_DEVICES value, e.g. 0, 1, or 0,1."
    ),
    cuda_home: Path | None = typer.Option(
        None,
        "--cuda-home",
        help="CUDA toolkit root containing bin/nvcc. Auto-detected when omitted.",
        resolve_path=True,
    ),
    gpu_memory_utilization: float | None = typer.Option(
        None, help="vLLM GPU memory fraction."
    ),
    max_model_len: int | None = typer.Option(
        None, help="Override vLLM max model length."
    ),
    pull: bool = typer.Option(
        True, "--pull/--no-pull", help="Download default asset if missing."
    ),
    background: bool = typer.Option(True, "--background/--foreground"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print command without starting vLLM."
    ),
    wait_timeout: int = typer.Option(
        600,
        "--wait-timeout",
        help="Seconds to wait for local vLLM /v1/models readiness.",
    ),
    extra_arg: list[str] | None = typer.Option(
        None, "--extra-arg", help="Extra vLLM arg. Repeatable."
    ),
) -> None:
    if backend != "vllm":
        raise typer.BadParameter("Only backend='vllm' is currently supported")
    if target == "all" and any([model_path, port, model_name]):
        raise typer.BadParameter(
            "When --target all is used, omit --model-path, --port and "
            "--model-name so each service can use its own defaults."
        )
    secret = api_key
    if secret is None:
        secret = (
            typer.prompt(
                "vLLM API key (leave blank for target default)",
                default="",
                hide_input=True,
                show_default=False,
            )
            or None
        )
    for item_target in expand_targets(target):
        progress_secrets = [secret] if secret else []
        wait_progress_callback = None
        if not dry_run and background:

            def wait_progress_callback(
                info: dict[str, Any], item_target: str = item_target
            ) -> None:
                _print_deploy_wait_progress(
                    item_target,
                    info,
                    progress_secrets,
                )

        def gpu_preflight_callback(
            info: dict[str, Any], item_target: str = item_target
        ) -> None:
            _print_gpu_preflight(item_target, info)

        def cuda_preflight_callback(
            info: dict[str, Any], item_target: str = item_target
        ) -> None:
            _print_cuda_preflight(item_target, info)

        try:
            result = deploy_vllm_service(
                workspace,
                target=item_target,
                model_path=model_path,
                manifest_file=manifest,
                vllm_command=vllm_command,
                host=host,
                public_host=public_host,
                port=port,
                api_key=secret,
                model_name=model_name,
                gpu=gpu,
                cuda_home=cuda_home,
                gpu_memory_utilization=gpu_memory_utilization,
                max_model_len=max_model_len,
                pull=pull,
                background=background,
                dry_run=dry_run,
                wait_timeout=wait_timeout,
                wait_progress_callback=wait_progress_callback,
                gpu_preflight_callback=gpu_preflight_callback,
                cuda_preflight_callback=cuda_preflight_callback,
                extra_args=extra_arg,
            )
        except RuntimeError as err:
            console.print(f"[red]Error:[/red] {escape(str(err))}")
            raise typer.Exit(code=1) from None
        console.print(
            _redacted_command(
                result["command"],
                cuda_visible_devices=result.get("cuda_visible_devices", ""),
                cuda_home=result.get("cuda_home", ""),
            )
        )
        if dry_run:
            continue
        console.print(
            f"[green]Deployed {item_target} SFT service[/green] "
            f"pid={result['pid']} base_url={result['base_url']}"
        )
    if dry_run:
        console.print("[yellow]Dry run only. Configuration was not changed.[/yellow]")


@models_app.command("status")
def models_status(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    table = Table(title="SFT Model Services")
    table.add_column("Target")
    table.add_column("Use SFT")
    table.add_column("Model")
    table.add_column("Base URL")
    table.add_column("PID")
    table.add_column("Log")
    for item in service_status(workspace):
        table.add_row(
            item["target"],
            str(item["use_sft"]),
            item["model_name"],
            item["base_url"],
            item["pid"],
            item["log"],
        )
    console.print(table)


@app.command("chat")
def chat(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    case: Path | None = typer.Option(
        None, "--case", help="Case file. Defaults to interactive.*."
    ),
    state: Path | None = typer.Option(
        None, "--state", help="Frozen prompt state JSON."
    ),
    save: Path | None = typer.Option(None, "--save", help="Save transcript JSONL."),
    debug_ui: bool = typer.Option(
        False,
        "--debug-ui",
        "--verbose",
        help="Show initialization steps and per-turn internal state.",
    ),
) -> None:
    _configure_chat_logging(debug_ui)
    _render_chat_header(debug_ui)
    console.print(Rule("[bold blue]Stage 1/2 · Initialize[/bold blue]"))
    _configure(workspace)
    init_events: list[tuple[str, str]] = []

    def progress(stage: str, detail: str) -> None:
        init_events.append((stage, detail))
        if debug_ui:
            console.print(f"[dim]• {escape(stage)}[/dim] {escape(detail)}")

    if state:
        _render_config_summary(
            workspace=workspace, source=state, source_kind="State", debug_ui=debug_ui
        )
        with console.status("[blue]加载冻结状态...[/blue]"):
            seeker = FrozenPromptSession(load_state(state))
        progress("state", "Frozen prompt session loaded")
    else:
        from .ms_patient import MsPatient

        case_path = case or _get_config_path(workspace)
        _render_config_summary(
            workspace=workspace, source=case_path, source_kind="Case", debug_ui=debug_ui
        )
        portrait, report, conversations = _load_seeker_data(case_path)
        if debug_ui:
            try:
                seeker = MsPatient(
                    portrait,
                    report,
                    conversations,
                    progress_callback=progress,
                )
            except Exception as err:
                if _looks_like_connection_error(err):
                    _print_model_connection_help(workspace, err)
                    raise typer.Exit(code=1) from None
                raise
        else:
            try:
                with console.status("[blue]初始化来访者状态...[/blue]"):
                    with _suppress_stdio(True):
                        seeker = MsPatient(
                            portrait,
                            report,
                            conversations,
                            progress_callback=progress,
                        )
            except Exception as err:
                if _looks_like_connection_error(err):
                    _print_model_connection_help(workspace, err)
                    raise typer.Exit(code=1) from None
                raise
    if debug_ui:
        _render_initialization_events(init_events)
    console.print(
        Panel(
            "[bold green]初始化完成[/bold green]\n"
            "来访者画像、历史记忆和对话状态已准备好。",
            border_style="green",
        )
    )
    _interactive_chat(seeker, save=save, debug_ui=debug_ui)


@app.command("demo")
def demo(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    case_file = workspace / "cases" / "family_stress_case.json"
    if not case_file.exists():
        write_case_json(sample_case(), case_file)
    chat(workspace=workspace, case=case_file, state=None, save=None, debug_ui=False)


@run_app.command("batch")
def run_batch(
    cases: list[str] = typer.Option(
        ..., "--case", help="Case file or glob. Repeatable."
    ),
    output: Path = typer.Option(Path("runs/batch"), "--out", "-o"),
    mode: str = typer.Option("prompt-only", help="prompt-only or full."),
    script: Path | None = typer.Option(
        None, "--script", help="JSON list of counselor messages."
    ),
    live: bool = typer.Option(
        False, "--live", help="Call the model for scripted conversations."
    ),
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    _configure(workspace)
    case_files = discover_case_files(cases, root=workspace)
    if not case_files:
        raise typer.BadParameter("No case files matched")
    messages = load_script_messages(script) if script else []
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.jsonl"
    for case_file in case_files:
        state = (
            build_full_state(case_file)
            if mode == "full"
            else build_prompt_only_state(case_file)
        )
        state_path = output / f"{state['case_id']}.state.json"
        save_state(state, state_path)
        record = {
            "case_id": state["case_id"],
            "state_file": str(state_path),
            "turns": [],
        }
        if live and messages:
            session = FrozenPromptSession(state)
            transcript_path = output / f"{state['case_id']}.transcript.jsonl"
            for message in messages:
                response = session.chat(message)
                append_jsonl(transcript_path, {"role": "Counselor", "content": message})
                append_jsonl(transcript_path, {"role": "Seeker", "content": response})
                record["turns"].append({"message": message, "response": response})
        append_jsonl(summary_path, record)
    console.print(
        f"[green]Batch complete[/green] cases={len(case_files)}, out={output}"
    )


@app.command("serve")
def serve_command(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    from .service import serve

    console.print(f"Serving AnnaAgent API on http://{host}:{port}")
    serve(workspace=workspace, host=host, port=port)


@logs_app.command("tail")
def logs_tail(
    file: Path = typer.Argument(Path("logs/anna-agent.log")),
    lines: int = typer.Option(50, "--lines", "-n"),
) -> None:
    if not file.exists():
        console.print(f"[yellow]Log file not found:[/yellow] {file}")
        return
    content = file.read_text(encoding="utf-8").splitlines()
    console.print("\n".join(content[-lines:]))


@cache_app.command("list")
def cache_list(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    cache = workspace / "cache"
    if not cache.exists():
        console.print("[yellow]No cache directory.[/yellow]")
        return
    for path in sorted(cache.rglob("*")):
        if path.is_file():
            console.print(path)


@cache_app.command("clean")
def cache_clean(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    cache = workspace / "cache"
    if not yes and not typer.confirm(f"Delete {cache}?", default=False):
        raise typer.Exit()
    shutil.rmtree(cache, ignore_errors=True)
    cache.mkdir(exist_ok=True)
    console.print("[green]Cache cleaned.[/green]")


@reset_app.command("workspace")
def reset_workspace(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    targets = [
        workspace / "runs",
        workspace / "outputs",
        workspace / "logs",
        workspace / "cache",
    ]
    if not yes and not typer.confirm(
        "Delete run/output/log/cache artifacts?", default=False
    ):
        raise typer.Exit()
    for target in targets:
        shutil.rmtree(target, ignore_errors=True)
        target.mkdir(exist_ok=True)
    console.print("[green]Workspace artifacts reset.[/green]")


def _print_hits(hits, seeker_id: str) -> None:
    if not hits:
        console.print("[yellow]No memory hits found.[/yellow]")
        return
    table = Table(title=f"Long-term memory hits for {seeker_id}")
    table.add_column("#", justify="right")
    table.add_column("Type")
    table.add_column("Session")
    table.add_column("Score", justify="right")
    table.add_column("Text")
    for index, hit in enumerate(hits, start=1):
        table.add_row(
            str(index),
            f"{hit.source_type}/{hit.memory_type}",
            hit.session_id,
            f"{hit.score:.4f}",
            hit.text[:240],
        )
    console.print(table)


def _redacted_command(
    command: list[str], cuda_visible_devices: str = "", cuda_home: str = ""
) -> str:
    redacted = []
    hide_next = False
    for item in command:
        if hide_next:
            redacted.append("***")
            hide_next = False
            continue
        redacted.append(item)
        if item in {"--api-key", "--api_key"}:
            hide_next = True
    prefixes = []
    if cuda_visible_devices:
        prefixes.append(f"CUDA_VISIBLE_DEVICES={cuda_visible_devices}")
    if cuda_home:
        prefixes.append(f"CUDA_HOME={cuda_home}")
    prefix = " ".join(prefixes)
    return f"{prefix} {' '.join(redacted)}" if prefix else " ".join(redacted)


def _redact_text(text: str, secrets: list[str]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "***")
    return redacted


if __name__ == "__main__":
    app()
