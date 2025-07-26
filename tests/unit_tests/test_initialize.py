import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import yaml

from anna_agent.config.initialize import initialize_project_at


def test_initialize_project(tmp_path: Path) -> None:
    initialize_project_at(tmp_path)
    settings = tmp_path / "settings.yaml"
    interactive = tmp_path / "interactive.yaml"
    assert settings.exists()
    assert interactive.exists()
    data = yaml.safe_load(interactive.read_text(encoding="utf-8"))
    assert "portrait" in data
    assert "report" in data
    assert "previous_conversations" in data
