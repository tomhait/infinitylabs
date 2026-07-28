#!/usr/bin/env python3
"""Exercise 1: Llama 3 agent with manual tool calling (no frameworks)."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
import json
import operator
import sys
from dataclasses import dataclass
from typing import Any, Callable

import requests
from zoneinfo import ZoneInfo


SYSTEM_PROMPT = """You are an assistant that can either answer directly or call tools.

You MUST always return exactly one JSON object, and nothing else.

Valid JSON outputs:
1) Final answer
{"type":"final_answer","content":"your answer"}

2) Tool call
{"type":"tool_call","tool":"calculator","arguments":{"expression":"(12+3)*4"}}
{"type":"tool_call","tool":"current_time","arguments":{"timezone":"Asia/Jerusalem"}}
{"type":"tool_call","tool":"unit_convert","arguments":{"value":10,"from_unit":"km","to_unit":"mi"}}

Rules:
- Use "calculator" for arithmetic or numeric computation.
- Use "current_time" when the user asks for current date/time.
- Use "unit_convert" for converting units like km/mi, C/F, kg/lb, m/ft.
- For conceptual/general questions, answer directly with "final_answer".
- Never hallucinate tool results.
- If a tool result is provided in the conversation, use it to produce a final answer.
- If you are unsure, prefer a tool call when computation is required.
"""


REPAIR_PROMPT = """Your previous response was invalid.
Return ONLY valid JSON matching one of these shapes:
{"type":"final_answer","content":"..."}
{"type":"tool_call","tool":"<tool_name>","arguments":{...}}
No markdown, no code fences, no extra text.
"""


class CalculatorError(ValueError):
    """Raised when expression is unsupported or unsafe."""


class UnitConversionError(ValueError):
    """Raised when a unit conversion request is unsupported."""


def safe_calculate(expression: str) -> float:
    """Safely evaluate a numeric expression with a strict AST whitelist."""
    if not expression or not expression.strip():
        raise CalculatorError("Expression is empty.")

    operators_map: dict[type[ast.AST], Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unary_map: dict[type[ast.AST], Callable[[Any], Any]] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in operators_map:
                raise CalculatorError(f"Operator not allowed: {op_type.__name__}")
            left = _eval(node.left)
            right = _eval(node.right)
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise CalculatorError("Division by zero is not allowed.")
            return float(operators_map[op_type](left, right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in unary_map:
                raise CalculatorError(f"Unary operator not allowed: {op_type.__name__}")
            return float(unary_map[op_type](_eval(node.operand)))
        raise CalculatorError(f"Unsupported expression node: {type(node).__name__}")

    try:
        parsed = ast.parse(expression, mode="eval")
        return _eval(parsed)
    except SyntaxError as error:
        raise CalculatorError(f"Invalid expression syntax: {error.msg}") from error


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


class Ex1Agent:
    def __init__(self, client: OllamaClient):
        self.client = client
        self.tools: dict[str, Callable[..., Any]] = {
            "calculator": self._tool_calculator,
            "current_time": self._tool_current_time,
            "unit_convert": self._tool_unit_convert,
        }

    def _tool_calculator(self, expression: str) -> dict[str, Any]:
        value = safe_calculate(expression)
        return {
            "expression": expression,
            "result": value,
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
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON from model: {error.msg}") from error

        if not isinstance(obj, dict):
            raise ValueError("Model output must be a JSON object.")
        output_type = obj.get("type")
        if output_type not in {"final_answer", "tool_call"}:
            raise ValueError("JSON 'type' must be 'final_answer' or 'tool_call'.")
        return obj

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

    def _execute_tool_call(self, action: dict[str, Any]) -> dict[str, Any]:
        tool_name = action.get("tool")
        args = action.get("arguments")

        if not isinstance(tool_name, str) or not tool_name:
            return {"error": "Invalid tool name."}
        if not isinstance(args, dict):
            return {"error": "Tool arguments must be an object."}
        if tool_name not in self.tools:
            return {"error": f"Unknown tool '{tool_name}'."}

        tool_fn = self.tools[tool_name]
        try:
            result = tool_fn(**args)
        except TypeError as error:
            return {"error": f"Tool arguments mismatch: {error}"}
        except CalculatorError as error:
            return {"error": str(error)}
        except UnitConversionError as error:
            return {"error": str(error)}
        except Exception as error:  # pragma: no cover
            return {"error": f"Tool execution failed: {error}"}
        return {"ok": result}

    def run(self, user_prompt: str, max_turns: int = 6) -> str:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(max_turns):
            raw = self.client.chat(messages)
            action = self._maybe_repair_response(messages, raw)

            if action["type"] == "final_answer":
                content = action.get("content")
                if not isinstance(content, str) or not content.strip():
                    return "Model returned an empty final answer."
                return content.strip()

            tool_result = self._execute_tool_call(action)
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
    parser = argparse.ArgumentParser(description="Exercise 1 Llama 3 agent (manual tools).")
    parser.add_argument("--prompt", type=str, help="Run one-shot prompt and exit.")
    parser.add_argument("--model", type=str, default="llama3", help="Ollama model name.")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL.",
    )
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds.")
    parser.add_argument("--max-turns", type=int, default=6, help="Maximum agent turns.")
    return parser


def run_interactive(agent: Ex1Agent, max_turns: int) -> None:
    print("Ex1 agent ready. Type 'exit' or 'quit' to stop.")
    while True:
        prompt = input("\nYou> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("Bye.")
            return
        if not prompt:
            continue
        try:
            answer = agent.run(prompt, max_turns=max_turns)
            print(f"Agent> {answer}")
        except Exception as error:
            print(f"Agent error: {error}")


def main() -> None:
    args = build_parser().parse_args()
    client = OllamaClient(model=args.model, base_url=args.base_url, timeout_seconds=args.timeout)
    agent = Ex1Agent(client)

    if args.prompt:
        try:
            print(agent.run(args.prompt, max_turns=args.max_turns))
        except Exception as error:
            print(f"Agent error: {error}")
            raise SystemExit(1) from error
        return

    run_interactive(agent, max_turns=args.max_turns)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
