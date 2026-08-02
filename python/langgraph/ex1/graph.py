from typing import TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int
    target: int


def increment(state: State) -> dict:
    value = state["value"] + 1
    print(f"  value -> {value}")
    return {"value": value}


def no_progress(state: State) -> dict:
    return {"value": state["value"]}


def route(state: State):
    if state["value"] >= state["target"]:
        return END
    return "step"


def build(node):
    g = StateGraph(State)
    g.add_node("step", node)
    g.add_edge(START, "step")
    g.add_conditional_edges("step", route)
    return g.compile()


def run_broken():
    print("\n=== Part (a): unreachable END ===")
    graph = build(no_progress)
    try:
        graph.invoke({"value": 0, "target": 5})
    except GraphRecursionError as e:
        print(f"GraphRecursionError: {e}")


def run_bandage():
    print("\n=== Band-aid: raise recursion_limit (still broken) ===")
    graph = build(no_progress)
    try:
        graph.invoke({"value": 0, "target": 5}, {"recursion_limit": 10})
    except GraphRecursionError as e:
        print(f"Still fails: {e}")


def run_fixed():
    print("\n=== Part (b): real fix — progress until target ===")
    graph = build(increment)
    result = graph.invoke({"value": 0, "target": 5})
    print(f"Final state: {result}")


if __name__ == "__main__":
    run_broken()
    run_bandage()
    run_fixed()
