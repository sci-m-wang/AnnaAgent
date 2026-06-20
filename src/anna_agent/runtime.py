import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .backbone import get_openai_client
from .case_data import load_case


def build_full_state(
    case_file: Path,
    progress_callback: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    from .ms_patient import MsPatient

    case = load_case(case_file)
    seeker = MsPatient(
        case["portrait"],
        case["report"],
        case["conversation"],
        progress_callback=progress_callback,
    )
    return {
        "schema_version": 1,
        "mode": "full",
        "case_id": case["id"],
        "seeker_id": case["seeker_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "portrait": case["portrait"],
        "report": case["report"],
        "previous_conversations": case["conversation"],
        "prompt": seeker.system,
        "complaint_chain": seeker.complaint_chain,
        "configuration": seeker.configuration,
        "metadata": {"source_file": str(case_file)},
    }


def save_state(state: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(path: Path) -> dict[str, Any]:
    state = json.loads(path.read_text(encoding="utf-8"))
    validate_state(state)
    return state


def validate_state(state: dict[str, Any]) -> None:
    if state.get("mode") == "prompt_only":
        raise ValueError(
            "prompt_only states are not supported. Run `anna init full` to "
            "generate a reusable prompt state, then load it with `anna chat --state`."
        )
    for key in ["prompt", "portrait", "report", "previous_conversations"]:
        if key not in state:
            raise ValueError(f"Frozen prompt state is missing '{key}'")


class FrozenPromptSession:
    def __init__(self, state: dict[str, Any]):
        validate_state(state)
        self.state = state
        self.messages: list[dict[str, str]] = []
        self.client = get_openai_client()

    def chat(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.state.get("model_name") or _configured_model_name(),
            messages=[{"role": "system", "content": self.state["prompt"]}]
            + self.messages,
        )
        content = response.choices[0].message.content or ""
        self.messages.append({"role": "assistant", "content": content})
        return content


def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": state.get("case_id", ""),
        "seeker_id": state.get("seeker_id", ""),
        "mode": state.get("mode", ""),
        "prompt_chars": len(state.get("prompt", "")),
        "previous_turns": len(state.get("previous_conversations", [])),
        "complaint_chain_items": len(state.get("complaint_chain", [])),
    }


def load_script_messages(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [
            item["content"] if isinstance(item, dict) else str(item) for item in raw
        ]
    if isinstance(raw, dict) and isinstance(raw.get("messages"), list):
        return [
            item["content"] if isinstance(item, dict) else str(item)
            for item in raw["messages"]
        ]
    raise ValueError("Script must be a JSON list or an object with a 'messages' list")


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(item, ensure_ascii=False) + "\n")


def _configured_model_name() -> str:
    from .common.registry import registry

    cfg = registry.get("anna_engine_config")
    return cfg.model_name
