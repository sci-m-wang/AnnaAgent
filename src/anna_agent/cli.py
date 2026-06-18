import json
import shutil
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
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
    deploy_vllm_service,
    expand_targets,
    service_status,
    set_sft_mode,
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


def _interactive_chat(seeker: Any, save: Path | None = None) -> None:
    while True:
        message = typer.prompt("请输入您的消息")
        if message.lower() in {"exit", "quit", "q"}:
            break
        try:
            response = seeker.chat(message)
        except Exception as err:
            console.print(f"[red]Error:[/red] {err}")
            continue
        if isinstance(response, tuple):
            response_text = response[0]
        else:
            response_text = response
        console.print(f"[bold]Counselor:[/bold] {message}")
        console.print(f"[bold green]Seeker:[/bold green] {response_text}")
        if save:
            append_jsonl(save, {"role": "Counselor", "content": message})
            append_jsonl(save, {"role": "Seeker", "content": response_text})


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
    chat(workspace=workspace, case=None, state=None, save=None)


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
        table.add_row(check.name, f"[{color}]{check.status}[/{color}]", check.detail)
    console.print(table)


@app.command("init")
def init_workspace(
    target: Path = typer.Argument(Path("anna-workspace"), help="Workspace directory."),
    force: bool = typer.Option(False, "--force", help="Overwrite generated files."),
) -> None:
    initialize_workspace(target, force=force)
    console.print(f"[green]Workspace initialized:[/green] {target}")


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
    state = build_full_state(case_file)
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
    host: str = typer.Option("127.0.0.1", help="vLLM bind host."),
    public_host: str = typer.Option("127.0.0.1", help="Host written to settings.yaml."),
    port: int | None = typer.Option(None, help="Service port. Defaults by target."),
    api_key: str | None = typer.Option(None, help="API key for vLLM service."),
    model_name: str | None = typer.Option(None, help="Served model name."),
    gpu: str | None = typer.Option(None, help="CUDA_VISIBLE_DEVICES value."),
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
        result = deploy_vllm_service(
            workspace,
            target=item_target,
            model_path=model_path,
            manifest_file=manifest,
            host=host,
            public_host=public_host,
            port=port,
            api_key=secret,
            model_name=model_name,
            gpu=gpu,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
            pull=pull,
            background=background,
            dry_run=dry_run,
            extra_args=extra_arg,
        )
        console.print(_redacted_command(result["command"]))
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
) -> None:
    _configure(workspace)
    if state:
        seeker = FrozenPromptSession(load_state(state))
    else:
        from .ms_patient import MsPatient

        case_path = case or _get_config_path(workspace)
        portrait, report, conversations = _load_seeker_data(case_path)
        seeker = MsPatient(portrait, report, conversations)
    _interactive_chat(seeker, save=save)


@app.command("demo")
def demo(
    workspace: Path = typer.Option(Path(), "--workspace", "--root", resolve_path=True),
) -> None:
    case_file = workspace / "cases" / "family_stress_case.json"
    if not case_file.exists():
        write_case_json(sample_case(), case_file)
    chat(workspace=workspace, case=case_file, state=None, save=None)


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


def _redacted_command(command: list[str]) -> str:
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
    return " ".join(redacted)


if __name__ == "__main__":
    app()
