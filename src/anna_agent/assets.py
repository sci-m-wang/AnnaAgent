import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from .workspace import default_asset_manifest


def manifest_path(workspace: Path, manifest_file: Path | None = None) -> Path:
    if manifest_file is not None:
        return manifest_file
    return workspace / "assets" / "anna-assets.json"


def load_manifest(workspace: Path, manifest_file: Path | None = None) -> dict[str, Any]:
    path = manifest_path(workspace, manifest_file)
    if not path.exists():
        return default_asset_manifest()
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(
    workspace: Path, manifest: dict[str, Any], manifest_file: Path | None = None
) -> None:
    path = manifest_path(workspace, manifest_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def resolve_asset_names(manifest: dict[str, Any], names: list[str]) -> list[str]:
    if not names:
        return [asset["name"] for asset in manifest.get("assets", [])]
    resolved: list[str] = []
    presets = manifest.get("presets", {})
    for name in names:
        if name in presets:
            resolved.extend(presets[name])
        else:
            resolved.append(name)
    return resolved


def list_assets(
    workspace: Path, manifest_file: Path | None = None
) -> list[dict[str, Any]]:
    manifest = load_manifest(workspace, manifest_file)
    return manifest.get("assets", [])


def pull_assets(
    workspace: Path,
    names: list[str],
    force: bool = False,
    manifest_file: Path | None = None,
    target_override: Path | None = None,
) -> list[dict[str, str]]:
    manifest = load_manifest(workspace, manifest_file)
    requested = list(dict.fromkeys(resolve_asset_names(manifest, names)))
    if target_override is not None and len(requested) != 1:
        raise ValueError("--target can only be used when pulling exactly one asset")
    assets = {asset["name"]: asset for asset in manifest.get("assets", [])}
    results: list[dict[str, str]] = []
    for name in requested:
        asset = assets.get(name)
        if not asset:
            results.append({"name": name, "status": "missing", "path": ""})
            continue
        if target_override is not None:
            asset = dict(asset)
            asset["target"] = str(target_override)
        results.extend(
            _pull_asset(
                workspace,
                asset,
                force=force,
                manifest_file=manifest_file,
            )
        )
    if manifest_file is None:
        save_manifest(workspace, manifest)
    return results


def find_asset(
    workspace: Path, name: str, manifest_file: Path | None = None
) -> dict[str, Any] | None:
    manifest = load_manifest(workspace, manifest_file)
    for asset in manifest.get("assets", []):
        if asset.get("name") == name:
            return asset
    return None


def resolve_asset_target(
    workspace: Path,
    asset: dict[str, Any],
    manifest_file: Path | None = None,
) -> Path:
    target = Path(asset.get("target", "assets"))
    if target.is_absolute():
        return target
    return _relative_target_base(workspace, manifest_file) / target


def _pull_asset(
    workspace: Path,
    asset: dict[str, Any],
    force: bool,
    manifest_file: Path | None = None,
) -> list[dict[str, str]]:
    source = asset.get("source", {})
    target = resolve_asset_target(workspace, asset, manifest_file)
    target.mkdir(parents=True, exist_ok=True)
    source_type = source.get("type")
    if source_type == "url":
        url = source.get("url", "")
        if not url:
            return [
                {"name": asset["name"], "status": "unconfigured", "path": str(target)}
            ]
        filename = source.get("filename") or Path(url).name
        return [_download(asset["name"], url, target / filename, force)]
    if source_type == "huggingface":
        repo_id = source.get("repo_id", "")
        revision = source.get("revision", "main")
        if not repo_id:
            return [
                {"name": asset["name"], "status": "unconfigured", "path": str(target)}
            ]
        if target.exists() and any(target.iterdir()) and not force:
            return [{"name": asset["name"], "status": "exists", "path": str(target)}]
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=repo_id,
            repo_type=source.get("repo_type"),
            revision=revision,
            local_dir=str(target),
            allow_patterns=source.get("allow_patterns"),
            ignore_patterns=source.get("ignore_patterns"),
        )
        return [{"name": asset["name"], "status": "downloaded", "path": str(target)}]
    return [
        {
            "name": asset.get("name", "asset"),
            "status": "unsupported",
            "path": str(target),
        }
    ]


def _relative_target_base(workspace: Path, manifest_file: Path | None) -> Path:
    if manifest_file is None:
        return workspace
    path = manifest_file.resolve()
    if path.parent.name == "assets":
        return path.parent.parent
    return path.parent


def _download(name: str, url: str, path: Path, force: bool) -> dict[str, str]:
    if path.exists() and not force:
        return {"name": name, "status": "exists", "path": str(path)}
    path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, path)
    return {
        "name": name,
        "status": "downloaded",
        "path": str(path),
        "sha256": _sha256(path),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
