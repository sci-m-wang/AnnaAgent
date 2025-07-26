import logging
from pathlib import Path

from .init_content import INIT_DOTENV, INIT_INTERACTIVE_YAML, INIT_YAML

logger = logging.getLogger(__name__)


def initialize_project_at(path: Path, force: bool = False) -> None:
    """Create default settings.yaml and .env at the given path."""
    logger.info("Initializing project at %s", path)
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)

    settings_yaml = root / "settings.yaml"
    if settings_yaml.exists() and not force:
        raise ValueError(f"Project already initialized at {root}")

    with settings_yaml.open("w", encoding="utf-8") as file:
        file.write(INIT_YAML)

    interactive_yaml = root / "interactive.yaml"
    if interactive_yaml.exists() and not force:
        raise ValueError(f"Project already initialized at {root}")

    with interactive_yaml.open("w", encoding="utf-8") as file:
        file.write(INIT_INTERACTIVE_YAML)

    dotenv = root / ".env"
    if not dotenv.exists() or force:
        with dotenv.open("w", encoding="utf-8") as file:
            file.write(INIT_DOTENV)
