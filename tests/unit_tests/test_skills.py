from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "patient-simulator"


def test_annaagent_skill_has_registry_ready_metadata():
    skill = SKILL_DIR / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "patient-simulator"
    assert "AnnaAgent" in metadata["description"]
    assert "seeker" in metadata["description"].lower()
    assert "prompt-only" in body
    assert "anna init full" in body
    assert "https://aclanthology.org/2025.findings-acl.1192/" in body
    assert "https://github.com/sci-m-wang/AnnaAgent" in body


def test_annaagent_skill_publication_references_exist():
    assert (SKILL_DIR / "references" / "cli-workflow.md").exists()
    assert (SKILL_DIR / "references" / "publishing.md").exists()
    assert (SKILL_DIR / "evals" / "evals.json").exists()
