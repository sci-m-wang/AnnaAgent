import json
from pathlib import Path
from typing import Any

import yaml

INTERACTIVE_CONFIG_FILES = ["interactive.yaml", "interactive.yml", "interactive.json"]


def get_interactive_config_path(root: Path) -> Path:
    for name in INTERACTIVE_CONFIG_FILES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Interactive config file not found in {root}")


def load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif path.suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported config extension: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError(f"Case file must contain a mapping: {path}")
    return data


def normalize_case(data: dict[str, Any], source_name: str = "case") -> dict[str, Any]:
    src = data.get("interactive", data)
    if not isinstance(src, dict):
        raise ValueError("The 'interactive' field must be a mapping")
    try:
        portrait = dict(src["portrait"])
        report = dict(src["report"])
        if "previous_conversations" in src:
            conversations = src["previous_conversations"]
        else:
            conversations = src["conversation"]
    except KeyError as exc:
        raise KeyError(
            "Config must contain 'portrait', 'report' and either "
            "'previous_conversations' or 'conversation'"
        ) from exc
    if "martial_status" not in portrait and "marital_status" in portrait:
        portrait["martial_status"] = portrait["marital_status"]
    case_id = str(src.get("id") or portrait.get("_case_id") or source_name)
    seeker_id = str(src.get("seeker_id") or portrait.get("_seeker_id") or case_id)
    portrait.setdefault("_case_id", case_id)
    portrait.setdefault("_seeker_id", seeker_id)
    return {
        "id": case_id,
        "seeker_id": seeker_id,
        "portrait": portrait,
        "report": report,
        "conversation": list(conversations),
    }


def load_case(path: Path) -> dict[str, Any]:
    return normalize_case(load_document(path), source_name=path.stem)


def load_seeker_data(path: Path) -> tuple[dict, dict, list]:
    case = load_case(path)
    return case["portrait"], case["report"], case["conversation"]


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    portrait = case.get("portrait")
    report = case.get("report")
    conversation = case.get("conversation") or case.get("previous_conversations")
    if not isinstance(portrait, dict):
        errors.append("portrait must be an object")
    if not isinstance(report, dict):
        errors.append("report must be an object")
    if not isinstance(conversation, list):
        errors.append("conversation or previous_conversations must be a list")
    else:
        for index, item in enumerate(conversation):
            if not isinstance(item, dict):
                errors.append(f"conversation[{index}] must be an object")
                continue
            if item.get("role") not in {"Seeker", "Counselor", "user", "assistant"}:
                errors.append(f"conversation[{index}].role is invalid or missing")
            if not isinstance(item.get("content"), str) or not item.get("content"):
                errors.append(
                    f"conversation[{index}].content must be a non-empty string"
                )
    if isinstance(portrait, dict):
        for key in ["age", "gender", "occupation", "symptoms"]:
            if key not in portrait:
                errors.append(f"portrait.{key} is missing")
        if "martial_status" not in portrait and "marital_status" not in portrait:
            errors.append(
                "portrait.martial_status or portrait.marital_status is missing"
            )
    return errors


def discover_case_files(patterns: list[str], root: Path | None = None) -> list[Path]:
    base = root or Path.cwd()
    files: list[Path] = []
    for pattern in patterns:
        path = Path(pattern)
        if path.is_file():
            files.append(path)
            continue
        matches = (
            sorted(base.glob(pattern))
            if not path.is_absolute()
            else sorted(path.parent.glob(path.name))
        )
        files.extend(
            match for match in matches if match.suffix in {".json", ".yaml", ".yml"}
        )
    unique: dict[str, Path] = {str(path.resolve()): path for path in files}
    return list(unique.values())


def sample_case() -> dict[str, Any]:
    return {
        "id": "42289a5f-bbdc-43f9-826a-9569bbbd5feb",
        "portrait": {
            "age": "35",
            "gender": "女",
            "martial_status": "已婚",
            "occupation": "行政人员",
            "symptoms": "胸闷、睡眠差、家庭压力、低落和无助感",
            "drisk": 2,
            "srisk": 1,
        },
        "report": {
            "案例标题": "家庭压力导致的心理困扰",
            "案例类别": ["家庭关系", "焦虑情绪"],
            "运用的技术": ["情绪聚焦", "认知重评"],
            "案例简述": ["来访者因家庭冲突和长期压力出现胸闷、睡眠差和无助感。"],
            "咨询经过": ["来访者描述与家人沟通时感到被忽视，并担心关系继续恶化。"],
            "经验感想": ["后续咨询可围绕压力来源、沟通边界和情绪调节展开。"],
        },
        "conversation": [
            {"role": "Seeker", "content": "心理咨询师，我觉得我的家庭让我压力很大。"},
            {"role": "Counselor", "content": "你能说说这种压力最明显的时候吗？"},
            {"role": "Seeker", "content": "我们经常因为小事争吵，我会胸闷，也睡不好。"},
            {"role": "Counselor", "content": "这些身体反应通常在争吵后出现吗？"},
        ],
    }


def write_case_json(case: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
