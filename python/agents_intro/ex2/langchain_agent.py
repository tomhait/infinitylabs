#!/usr/bin/env python3
"""Exercise 2: Ex1 behavior rebuilt with LangChain + local Ollama."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
import json
import operator
import re
import sys
import warnings
from typing import Any, Callable
from zoneinfo import ZoneInfo

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


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
- For arithmetic or numeric computation, you MUST call "calculator".
- For current date/time requests, you MUST call "current_time".
- For converting units like km/mi, C/F, kg/lb, m/ft, you MUST call "unit_convert".
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

EMPTY_ANSWER_REPAIR_PROMPT = """Your JSON used type=final_answer but content was empty or missing.
Return ONLY valid JSON with a non-empty string:
{"type":"final_answer","content":"..."}
No markdown, no extra text.
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


class LangChainAgent:
    def __init__(self, model: str, base_url: str, timeout_seconds: int):
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0,
            timeout=timeout_seconds,
        )
        self.tools: dict[str, Callable[..., Any]] = {
            "calculator": self._tool_calculator,
            "current_time": self._tool_current_time,
            "unit_convert": self._tool_unit_convert,
        }

    def _tool_calculator(self, expression: str) -> dict[str, Any]:
        value = safe_calculate(expression)
        return {"expression": expression, "result": value}

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

    def _invoke_llm(self, messages: list[Any]) -> str:
        try:
            response = self.llm.invoke(messages)
        except Exception as error:
            raise RuntimeError(
                "Failed to call Ollama through LangChain. "
                "Ensure Ollama is running and the model is available."
            ) from error
        if not isinstance(response, AIMessage):
            raise RuntimeError("Unexpected non-AI response from model.")
        if not isinstance(response.content, str):
            raise RuntimeError("Model response content is not plain text.")
        return response.content.strip()

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

    def _maybe_repair_response(self, messages: list[Any], raw: str) -> dict[str, Any]:
        try:
            return self._parse_json_response(raw)
        except ValueError:
            repair_messages = messages + [
                AIMessage(content=raw),
                HumanMessage(content=REPAIR_PROMPT),
            ]
            repaired = self._invoke_llm(repair_messages)
            return self._parse_json_response(repaired)

    def _execute_tool_call(self, action: dict[str, Any]) -> dict[str, Any]:
        tool_name = action.get("tool")
        args = action.get("arguments")
        if not isinstance(tool_name, str) or not tool_name:
            return {"error": "Invalid tool name."}
        if not isinstance(args, dict):
            return {"error": "Tool arguments must be an object."}
        if tool_name not in self.tools:
            return {"error": f"Unknown tool '{tool_name}'."}

        try:
            result = self.tools[tool_name](**args)
        except TypeError as error:
            return {"error": f"Tool arguments mismatch: {error}"}
        except (CalculatorError, UnitConversionError, ValueError) as error:
            return {"error": str(error)}
        except Exception as error:  # pragma: no cover
            return {"error": f"Tool execution failed: {error}"}
        return {"ok": result}

    def _required_tool_for_prompt(self, prompt: str) -> str | None:
        text = prompt.lower()
        if "time" in text or "date" in text or "timezone" in text:
            return "current_time"
        if "convert" in text:
            return "unit_convert"
        if re.search(r"[\d\)\(][\s]*[\+\-\*/]", text):
            return "calculator"
        return None

    def run(self, user_prompt: str, max_turns: int = 6) -> str:
        messages: list[Any] = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        required_tool = self._required_tool_for_prompt(user_prompt)
        used_tools: set[str] = set()

        for _ in range(max_turns):
            raw = self._invoke_llm(messages)
            action = self._maybe_repair_response(messages, raw)

            if action["type"] == "final_answer":
                if required_tool and required_tool not in used_tools:
                    messages.append(AIMessage(content=raw))
                    messages.append(
                        HumanMessage(
                            content=(
                                f"You must call '{required_tool}' before giving final_answer "
                                "for this user request. Return a tool_call JSON now."
                            )
                        )
                    )
                    continue
                content = action.get("content")
                if not isinstance(content, str) or not content.strip():
                    repair_messages = messages + [
                        AIMessage(content=raw),
                        HumanMessage(content=EMPTY_ANSWER_REPAIR_PROMPT),
                    ]
                    repaired = self._invoke_llm(repair_messages)
                    repaired_action = self._parse_json_response(repaired)
                    repaired_content = repaired_action.get("content")
                    if isinstance(repaired_content, str) and repaired_content.strip():
                        return repaired_content.strip()
                    return "Model returned an empty final answer."
                return content.strip()

            tool_result = self._execute_tool_call(action)
            tool_name = action.get("tool")
            if isinstance(tool_name, str):
                used_tools.add(tool_name)
            messages.append(AIMessage(content=json.dumps(action)))
            messages.append(
                HumanMessage(
                    content=(
                        "Tool execution result (JSON): "
                        + json.dumps(tool_result, ensure_ascii=True)
                        + "\nIf computation is complete, return final_answer."
                    )
                )
            )

        return "Agent stopped after max turns without final_answer."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exercise 2 LangChain agent with local Ollama.")
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


def run_interactive(agent: LangChainAgent, max_turns: int) -> None:
    print("Ex2 LangChain agent ready. Type 'exit' or 'quit' to stop.")
    while True:
        prompt = input("\nYou> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("Bye.")
            return
        if not prompt:
            continue
        try:
            print(f"Agent> {agent.run(prompt, max_turns=max_turns)}")
        except Exception as error:
            print(f"Agent error: {error}")


def main() -> None:
    args = build_parser().parse_args()
    agent = LangChainAgent(
        model=args.model,
        base_url=args.base_url,
        timeout_seconds=args.timeout,
    )

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
