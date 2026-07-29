import ast
import operator
import re
from dataclasses import dataclass, field

from mcp.server.fastmcp import Context, FastMCP

HOST = "127.0.0.1"
PORT = 8765

mcp = FastMCP("calculator", host=HOST, port=PORT)

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class SessionState:
    last_result: float | int | None = None
    symbols: dict[str, float | int] = field(default_factory=dict)


_sessions: dict[int, SessionState] = {}


def _session_state(ctx: Context) -> SessionState:
    key = id(ctx.session)
    state = _sessions.get(key)
    if state is None:
        state = SessionState()
        _sessions[key] = state
    return state


def _eval_node(node: ast.AST, symbols: dict[str, float | int]) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, symbols)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in symbols:
            raise NameError(f"undefined variable: {node.id}")
        return symbols[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](
            _eval_node(node.left, symbols),
            _eval_node(node.right, symbols),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand, symbols))
    raise ValueError("unsupported expression")


def evaluate(expression: str, symbols: dict[str, float | int]) -> float | int:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree, symbols)


@mcp.tool()
def let(name: str, value: float, ctx: Context) -> float | int:
    """Store a numeric variable in this session's symbol table."""
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"invalid variable name: {name!r}")
    number: float | int = int(value) if float(value).is_integer() else float(value)
    state = _session_state(ctx)
    state.symbols[name] = number
    return number


@mcp.tool()
def calculate(expression: str, ctx: Context) -> float | int:
    """Evaluate an arithmetic expression, optionally using session variables."""
    state = _session_state(ctx)
    result = evaluate(expression, state.symbols)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    state.last_result = result
    return result


@mcp.tool()
def last_result(ctx: Context) -> float | int:
    """Return the result of the last calculate call in this session."""
    state = _session_state(ctx)
    if state.last_result is None:
        raise ValueError("no calculation has been performed yet")
    return state.last_result


@mcp.tool()
def state(ctx: Context) -> dict:
    """Return last_result and the symbol table for this session."""
    session = _session_state(ctx)
    return {
        "last_result": session.last_result,
        "symbols": dict(session.symbols),
    }


if __name__ == "__main__":
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("GoodBye :)")
