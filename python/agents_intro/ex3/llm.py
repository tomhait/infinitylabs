"""Shared LangChain + Ollama helpers for Ex3 agents."""

from __future__ import annotations

import json
import re
import warnings
from typing import Any

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


def build_llm(model: str, base_url: str, timeout: int, temperature: float = 0.2) -> ChatOllama:
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        timeout=timeout,
    )


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model text, tolerating optional code fences."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model response.")
        candidate = cleaned[start : end + 1]

    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as error:
        # Common LLM issue: trailing commas.
        fixed = re.sub(r",\s*}", "}", candidate)
        fixed = re.sub(r",\s*]", "]", fixed)
        try:
            obj = json.loads(fixed)
        except json.JSONDecodeError as second_error:
            raise ValueError(
                f"Invalid JSON ({second_error.msg} at line {second_error.lineno} col {second_error.colno}). "
                f"Snippet: {candidate[:180]!r}"
            ) from error

    if not isinstance(obj, dict):
        raise ValueError("Expected a JSON object.")
    return obj


def extract_python_and_json(text: str) -> tuple[str, dict[str, Any]]:
    """
    Parse dual-block responses:
      ```python
      ...
      ```
      ```json
      {...}
      ```
    """
    code_match = re.search(r"```python\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if not code_match:
        # Fallback markers.
        marker = re.search(
            r"<<<CODE>>>\s*(.*?)\s*<<<END_CODE>>>",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not marker:
            raise ValueError("No python code block found (expected ```python ... ```).")
        code = marker.group(1).strip()
    else:
        code = code_match.group(1).strip()

    json_match = re.search(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if json_match:
        meta = extract_json_object("```json\n" + json_match.group(1).strip() + "\n```")
    else:
        marker = re.search(
            r"<<<JSON>>>\s*(.*?)\s*<<<END_JSON>>>",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if marker:
            meta = extract_json_object(marker.group(1))
        else:
            # Last resort: parse trailing JSON object.
            meta = extract_json_object(text)

    if not code:
        raise ValueError("Extracted python code block is empty.")
    return code, meta


def chat_text(llm: ChatOllama, system_prompt: str, user_prompt: str) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return _content_to_text(getattr(response, "content", response)).strip()


def chat_json(
    llm: ChatOllama,
    system_prompt: str,
    user_prompt: str,
    *,
    repair_hint: str | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Call the LLM and require a JSON object response with repair retries."""
    messages: list[Any] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = llm.invoke(messages)
            raw = _content_to_text(getattr(response, "content", response))
            return extract_json_object(raw)
        except Exception as error:
            last_error = error
            if attempt >= max_attempts:
                break
            hint = repair_hint or "Return ONLY a valid JSON object."
            messages.extend(
                [
                    AIMessage(content=raw if "raw" in locals() else ""),
                    HumanMessage(
                        content=(
                            f"Attempt {attempt} failed: {error}\n"
                            f"{hint}\n"
                            "Return ONLY valid JSON. No markdown, no code fences."
                        )
                    ),
                ]
            )
    assert last_error is not None
    raise last_error


def chat_python_and_json(
    llm: ChatOllama,
    system_prompt: str,
    user_prompt: str,
    *,
    repair_hint: str | None = None,
    max_attempts: int = 3,
) -> tuple[str, dict[str, Any]]:
    """Call the LLM and parse a python fence + json fence response."""
    messages: list[Any] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    last_error: Exception | None = None
    raw = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = llm.invoke(messages)
            raw = _content_to_text(getattr(response, "content", response))
            return extract_python_and_json(raw)
        except Exception as error:
            last_error = error
            if attempt >= max_attempts:
                break
            hint = repair_hint or "Return ```python``` then ```json``` blocks."
            messages.extend(
                [
                    AIMessage(content=raw),
                    HumanMessage(
                        content=(
                            f"Attempt {attempt} failed: {error}\n"
                            f"{hint}\n"
                            "Important: put Python source ONLY in the python fence. "
                            "Put metadata/bugs ONLY in the json fence. "
                            "Do NOT put Python source inside JSON."
                        )
                    ),
                ]
            )
    assert last_error is not None
    raise ValueError(f"{last_error} | last_response_snippet={raw[:300]!r}") from last_error
