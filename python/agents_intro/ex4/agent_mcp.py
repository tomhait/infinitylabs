#!/usr/bin/env python3
"""Exercise 4: Ex1 agent with calculator tools routed over MCP (ex3_mcp server)."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable

import requests
from mcp import ClientSession
from zoneinfo import ZoneInfo

from mcp_tools import DEFAULT_MCP_URL, MCP_CALCULATOR_TOOLS, call_tool, mcp_session


SYSTEM_PROMPT = """You are an assistant that can either answer directly or call tools.

You MUST always return exactly one JSON object, and nothing else.

Valid JSON outputs:
1) Final answer
{"type":"final_answer","content":"your answer"}

2) Tool call (session calculator over MCP)
{"type":"tool_call","tool":"let","arguments":{"name":"x","value":10}}
{"type":"tool_call","tool":"calculate","arguments":{"expression":"x+5*2"}}
{"type":"tool_call","tool":"last_result","arguments":{}}
{"type":"tool_call","tool":"state","arguments":{}}

Other local tools:
{"type":"tool_call","tool":"current_time","arguments":{"timezone":"Asia/Jerusalem"}}
{"type":"tool_call","tool":"unit_convert","arguments":{"value":10,"from_unit":"km","to_unit":"mi"}}

Rules:
- For arithmetic, use MCP calculator tools:
  - "let" to define variables in the current session
  - "calculate" to evaluate expressions (can use let variables)
  - "last_result" to read the previous calculate result
  - "state" to inspect session symbols and last_result
- Use "current_time" when the user asks for current date/time.
- Use "unit_convert" for converting units like km/mi, C/F, kg/lb, m/ft.
- For conceptual/general questions, answer directly with "final_answer".
- Never hallucinate tool results.
- If a tool result is provided in the conversation, use it to produce a final answer.
- If variables are needed, call "let" before "calculate".
- Pass the FULL expression to calculate exactly as requested (e.g. "x*5+10", not just "x*5").
- After a successful calculate tool result, use that numeric result in final_answer.
"""


def _expected_calculate_expression(prompt: str) -> str | None:
    match = re.search(r"\bcalculate\s+([^,?.]+)", prompt, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _expected_let_bindings(prompt: str) -> list[tuple[str, float]]:
    bindings: list[tuple[str, float]] = []
    for match in re.finditer(
        r"\b(?:let\s+)?([A-Za-z_]\w*)\s+be\s+(-?\d+(?:\.\d+)?)",
        prompt,
        re.IGNORECASE,
    ):
        bindings.append((match.group(1), float(match.group(2))))
    return bindings


def _normalize_expr(expr: str) -> str:
    return re.sub(r"\s+", "", expr.lower())


def _calculation_hint(prompt: str) -> str:
    expr = _expected_calculate_expression(prompt)
    if not expr:
        return ""
    return f"\n\nImportant: call calculate with the full expression exactly: {expr}"


REPAIR_PROMPT = """Your previous response was invalid.
Return ONLY valid JSON matching one of these shapes:
{"type":"final_answer","content":"..."}
{"type":"tool_call","tool":"<tool_name>","arguments":{...}}
No markdown, no code fences, no extra text.
"""


class UnitConversionError(ValueError):
    """Raised when a unit conversion request is unsupported."""


@dataclass
class OllamaClient:
    model: str = "llama3"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 60

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        url = f"{self.base_url.rstrip('/')}/api/chat"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                "Failed to call Ollama API. Ensure Ollama is running and model is available."
            ) from error

        data = response.json()
        message = data.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama response does not contain message.content text.")
        return content.strip()


class AgentMCP:
    def __init__(self, client: OllamaClient, mcp: ClientSession, *, debug: bool = False):
        self.client = client
        self.mcp = mcp
        self.debug = debug
        self.local_tools: dict[str, Callable[..., Any]] = {
            "current_time": self._tool_current_time,
            "unit_convert": self._tool_unit_convert,
        }

    def _tool_current_time(self, timezone: str | None = None) -> dict[str, Any]:
        if timezone:
            try:
                now = datetime.now(ZoneInfo(timezone))
            except Exception as error:
                raise ValueError(f"Invalid timezone '{timezone}': {error}") from error
            tz_name = timezone
        else:
            now = datetime.now().astimezone()
            tz_name = str(now.tzinfo)

        return {
            "iso": now.isoformat(),
            "timezone": tz_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }

    def _tool_unit_convert(self, value: float, from_unit: str, to_unit: str) -> dict[str, Any]:
        normalized_from = from_unit.strip().lower()
        normalized_to = to_unit.strip().lower()
        number = float(value)

        conversions: dict[tuple[str, str], Callable[[float], float]] = {
            ("km", "mi"): lambda v: v * 0.621371,
            ("mi", "km"): lambda v: v / 0.621371,
            ("kg", "lb"): lambda v: v * 2.2046226218,
            ("lb", "kg"): lambda v: v / 2.2046226218,
            ("m", "ft"): lambda v: v * 3.280839895,
            ("ft", "m"): lambda v: v / 3.280839895,
            ("c", "f"): lambda v: (v * 9 / 5) + 32,
            ("f", "c"): lambda v: (v - 32) * 5 / 9,
        }

        if normalized_from == normalized_to:
            converted = number
        else:
            key = (normalized_from, normalized_to)
            if key not in conversions:
                supported = ", ".join([f"{a}->{b}" for (a, b) in conversions])
                raise UnitConversionError(
                    f"Unsupported conversion '{normalized_from}->{normalized_to}'. "
                    f"Supported: {supported}"
                )
            converted = conversions[key](number)

        return {
            "input": {"value": number, "unit": normalized_from},
            "output": {"value": round(converted, 6), "unit": normalized_to},
        }

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        decoder = json.JSONDecoder()
        start = cleaned.find("{")
        while start != -1:
            try:
                obj, _ = decoder.raw_decode(cleaned[start:])
            except json.JSONDecodeError:
                start = cleaned.find("{", start + 1)
                continue
            if not isinstance(obj, dict):
                raise ValueError("Model output must be a JSON object.")
            output_type = obj.get("type")
            if output_type not in {"final_answer", "tool_call"}:
                raise ValueError("JSON 'type' must be 'final_answer' or 'tool_call'.")
            return obj
        raise ValueError("No JSON object found in model response.")

    def _maybe_repair_response(self, messages: list[dict[str, str]], raw: str) -> dict[str, Any]:
        try:
            return self._parse_json_response(raw)
        except ValueError:
            repair_messages = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": REPAIR_PROMPT},
            ]
            repaired_raw = self.client.chat(repair_messages)
            return self._parse_json_response(repaired_raw)

    async def _execute_tool_call(self, action: dict[str, Any]) -> dict[str, Any]:
        tool_name = action.get("tool")
        args = action.get("arguments")

        if not isinstance(tool_name, str) or not tool_name:
            return {"error": "Invalid tool name."}
        if not isinstance(args, dict):
            return {"error": "Tool arguments must be an object."}

        try:
            if tool_name in MCP_CALCULATOR_TOOLS:
                result = await call_tool(self.mcp, tool_name, args)
                return {"ok": result}
            if tool_name in self.local_tools:
                result = self.local_tools[tool_name](**args)
                return {"ok": result}
            return {"error": f"Unknown tool '{tool_name}'."}
        except TypeError as error:
            return {"error": f"Tool arguments mismatch: {error}"}
        except UnitConversionError as error:
            return {"error": str(error)}
        except Exception as error:
            return {"error": f"Tool execution failed: {error}"}

    async def run(self, user_prompt: str, max_turns: int = 8) -> str:
        expected_expr = _expected_calculate_expression(user_prompt)
        expected_lets = _expected_let_bindings(user_prompt)
        last_calculate_result: Any | None = None

        for name, value in expected_lets:
            result = await call_tool(self.mcp, "let", {"name": name, "value": value})
            if self.debug:
                print(f"[mcp] let {name}={value} -> {result}")

        augmented_prompt = user_prompt + _calculation_hint(user_prompt)
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": augmented_prompt},
        ]

        for _ in range(max_turns):
            raw = self.client.chat(messages)
            action = self._maybe_repair_response(messages, raw)
            if self.debug:
                print(f"[llm] {json.dumps(action, ensure_ascii=True)}")

            if action["type"] == "final_answer":
                if expected_expr and last_calculate_result is None:
                    tool_result = await self._execute_tool_call(
                        {"tool": "calculate", "arguments": {"expression": expected_expr}}
                    )
                    if "ok" in tool_result:
                        last_calculate_result = tool_result["ok"]
                        if self.debug:
                            print(f"[mcp] auto calculate -> {expected_expr} = {last_calculate_result}")
                        return str(last_calculate_result)

                content = action.get("content")
                if not isinstance(content, str) or not content.strip():
                    return "Model returned an empty final answer."
                if last_calculate_result is not None and (
                    "exact numeric" in user_prompt.lower() or expected_expr is not None
                ):
                    return str(last_calculate_result)
                return content.strip()

            tool_result = await self._execute_tool_call(action)
            if action.get("tool") == "calculate" and expected_expr:
                called_expr = str(action.get("arguments", {}).get("expression", ""))
                if _normalize_expr(called_expr) != _normalize_expr(expected_expr):
                    tool_result = await self._execute_tool_call(
                        {"tool": "calculate", "arguments": {"expression": expected_expr}}
                    )
                    if self.debug:
                        print(f"[mcp] corrected calculate -> {expected_expr}")

            if action.get("tool") == "calculate" and "ok" in tool_result:
                last_calculate_result = tool_result["ok"]

            if self.debug:
                print(f"[tool] {json.dumps(tool_result, ensure_ascii=True)}")

            messages.append({"role": "assistant", "content": json.dumps(action)})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool execution result (JSON): "
                        + json.dumps(tool_result, ensure_ascii=True)
                        + "\nIf computation is complete, return final_answer."
                    ),
                }
            )

        return "Agent stopped after max turns without final_answer."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise 4 agent: Ex1 loop with MCP session calculator."
    )
    parser.add_argument("--prompt", type=str, help="Run one-shot prompt and exit.")
    parser.add_argument("--model", type=str, default="llama3", help="Ollama model name.")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL.",
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        default=DEFAULT_MCP_URL,
        help="MCP calculator server URL.",
    )
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds.")
    parser.add_argument("--max-turns", type=int, default=8, help="Maximum agent turns.")
    parser.add_argument("--debug", action="store_true", help="Print tool/LLM steps.")
    return parser


async def run_interactive(agent: AgentMCP, max_turns: int) -> None:
    print("Ex4 MCP agent ready. Type 'exit' or 'quit' to stop.")
    while True:
        prompt = input("\nYou> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("Bye.")
            return
        if not prompt:
            continue
        try:
            answer = await agent.run(prompt, max_turns=max_turns)
            print(f"Agent> {answer}")
        except Exception as error:
            print(f"Agent error: {error}")


async def async_main(args: argparse.Namespace) -> None:
    client = OllamaClient(model=args.model, base_url=args.base_url, timeout_seconds=args.timeout)
    async with mcp_session(args.mcp_url) as session:
        agent = AgentMCP(client, session, debug=args.debug)
        if args.prompt:
            print(await agent.run(args.prompt, max_turns=args.max_turns))
            return
        await run_interactive(agent, max_turns=args.max_turns)


def _unwrap_error(error: BaseException) -> BaseException:
    if isinstance(error, ExceptionGroup) and error.exceptions:
        return _unwrap_error(error.exceptions[0])
    return error


def main() -> None:
    args = build_parser().parse_args()
    try:
        asyncio.run(async_main(args))
    except Exception as error:
        root = _unwrap_error(error)
        print(f"Agent error: {root}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
