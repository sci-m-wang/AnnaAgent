import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple


class DatasetLoader:
    """
    负责加载并按患者 id 建立索引的读取器，带 mtime 热加载与统计能力。

    期望数据结构（每条记录至少包含 id，其他键根据项目而定）：
    {
      "id": "<patient_id>",
      "portrait": {...},
      "report": {...},
      "previous_conversations": [...],  # 可选，兼容 "conversation"
      ...
    }
    """

    def __init__(self, dataset_path: Path):
        self._dataset_path = Path(dataset_path)
        self._lock = threading.Lock()
        self._mtime: float = 0.0
        self._id_to_record: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _load_from_disk(self) -> None:
        with self._lock:
            if not self._dataset_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {self._dataset_path}")
            mtime = self._dataset_path.stat().st_mtime
            if self._loaded and mtime == self._mtime:
                return
            with self._dataset_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # 支持数组或字典形式，若为字典尝试从 values 取
            records: List[Dict[str, Any]]
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # 若是 {id: record} 结构
                if all(isinstance(v, dict) for v in data.values()):
                    records = list(data.values())
                else:
                    raise ValueError(
                        "Unsupported dataset dict structure; expected {id: record}"
                    )
            else:
                raise ValueError("Unsupported dataset type; expected list or dict")

            id_to_record: Dict[str, Dict[str, Any]] = {}
            for rec in records:
                if not isinstance(rec, dict) or "id" not in rec:
                    continue
                pid = str(rec["id"])  # 统一为字符串 key
                id_to_record[pid] = rec

            self._id_to_record = id_to_record
            self._mtime = mtime
            self._loaded = True

    def _ensure_loaded(self) -> None:
        # 简单的 mtime 触发热加载
        try:
            mtime = self._dataset_path.stat().st_mtime
        except FileNotFoundError:
            # 延迟到真正访问时报错
            mtime = 0.0
        if not self._loaded or mtime != self._mtime:
            self._load_from_disk()

    def get_by_id(self, patient_id: str) -> Dict[str, Any]:
        self._ensure_loaded()
        pid = str(patient_id)
        try:
            return self._id_to_record[pid]
        except KeyError:
            raise KeyError(f"Patient id not found: {patient_id}")

    def _normalize_portrait(self, portrait: Any) -> Dict[str, Any]:
        # 兼容非字典输入，统一为字典
        p = dict(portrait) if isinstance(portrait, dict) else {}
        # 别名兼容：marital_status -> martial_status
        if "martial_status" not in p and "marital_status" in p:
            p["martial_status"] = p.get("marital_status")
        # 填充默认值以满足 PatientProfile 模型
        p.setdefault("age", "28")
        p.setdefault("gender", "男")
        p.setdefault("occupation", "未知")
        p.setdefault("martial_status", "未婚")
        p.setdefault("symptoms", "工作焦虑，失眠")
        return p

    def try_map_to_components(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], Any, Any]:
        """
        将一条记录映射为 (portrait, report, previous_conversations, seeker_prompt, chain)。
        兼容键名差异，确保画像字段完整。
        """
        conversation = record.get("previous_conversations")
        if conversation is None:
            conversation = record.get("conversation", [])
        if conversation is None:
            conversation = []

        report = record.get("report", {})
        portrait = self._normalize_portrait(record.get("portrait"))

        seeker_prompt = (
            record.get("seeker_prompt")
            or record.get("seek_prompt")
            or record.get("prompt")
            or record.get("system")
        )
        
        # 如果没有找到seeker_prompt，使用默认的病人角色设定
        if not seeker_prompt:
            portrait_info = self._normalize_portrait(record.get("portrait", {}))
            seeker_prompt = f"""
# Role: 心理咨询患者

## Profile
- 性别: {portrait_info.get('gender', '未知')}
- 年龄: {portrait_info.get('age', '未知')}
- 职业: {portrait_info.get('occupation', '未知')}
- 婚姻状况: {portrait_info.get('martial_status', '未知')}

## Situation
- 你是一个有心理障碍的患者，正在向心理咨询师求助，在咨询师的引导和帮助下解决自己的困惑
- 你的主要症状包括：{portrait_info.get('symptoms', '心理困扰')}

## Characteristics of speaking style
- 情绪低落，寡言少语，回复风格表现心情不振奋
- 表达情绪真实，通过具体实例传达内心感受
- 对自身的疑惑和不安能够坦诚表达
- 采用反思的语气，愿意探讨内心深处的问题
- 对解决方案表现出一定的开放性和期待

## Constraints
- 你对咨询师有一种抵触情绪，不太愿意接受他人的帮助
- 你是一个遇到心理健康问题的求助者，需要真正的帮助和情绪支持，如果咨询师的回应不理想，要勇于表达自己的困惑和不满
- 一次不能提及过多的症状信息，每轮最多讨论一个症状
- 你应该用含糊和口语化的方式表达你的症状，并将其与你的生活经历联系起来，不要使用专业术语

## OutputFormat:
- 语言：Chinese
- 不超过200字
- 口语对话风格，仅包含对话内容
"""
        chain = record.get("chain") or record.get("complaint_chain") or []

        return portrait, report, conversation, seeker_prompt, chain

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._id_to_record)

    def list_ids(self) -> List[str]:
        self._ensure_loaded()
        return list(self._id_to_record.keys())

    @property
    def dataset_path(self) -> Path:
        return self._dataset_path


