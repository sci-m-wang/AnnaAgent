import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
import yaml

from anna_agent.cli import _get_config_path, _load_seeker_data


def test_load_seeker_data_yaml_root(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "portrait": {"age": "20"},
                "report": {},
                "previous_conversations": [],
            }
        ),
        encoding="utf-8",
    )
    portrait, report, conv = _load_seeker_data(cfg)
    assert portrait["age"] == "20"
    assert report == {}
    assert conv == []


def test_load_seeker_data_yaml_nested(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "interactive": {
                    "portrait": {"age": "20"},
                    "report": {"x": 1},
                    "previous_conversations": [
                        {"role": "a", "content": "b"}
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    portrait, report, conv = _load_seeker_data(cfg)
    assert portrait["age"] == "20"
    assert report == {"x": 1}
    assert conv[0]["role"] == "a"


def test_load_seeker_data_missing(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("portrait: {}", encoding="utf-8")
    with pytest.raises(KeyError):
        _load_seeker_data(cfg)


def test_get_config_path_default(tmp_path: Path) -> None:
    """_get_config_path should prefer interactive.yaml if present."""
    interactive = tmp_path / "interactive.yaml"
    interactive.write_text("portrait: {}\nreport: {}\nprevious_conversations: []", encoding="utf-8")
    path = _get_config_path(tmp_path, None)
    assert path == interactive
