import json
from typing import Any


def extract_tool_call_arguments(response: Any) -> dict[str, Any] | None:
    """Return the first tool-call arguments as JSON, or None if absent/invalid."""

    try:
        choices = getattr(response, "choices", None)
        if not choices:
            return None
        message = choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            arguments = tool_calls[0].function.arguments
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else None
        content = getattr(message, "content", None)
        if not isinstance(content, str) or not content.strip():
            return None
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except (AttributeError, IndexError, KeyError, TypeError, json.JSONDecodeError):
        return None
