from pathlib import Path


def initialize_project_at(path: Path, force: bool = False) -> None:
    """Create an AnnaAgent workspace at the given path."""
    from ..workspace import initialize_workspace

    initialize_workspace(path, force=force)
