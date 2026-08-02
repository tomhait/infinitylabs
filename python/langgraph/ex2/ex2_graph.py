import operator
from typing import Annotated, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph


class BrokenState(TypedDict):
    values: list


class FixedState(TypedDict):
    values: Annotated[list, operator.add]


def left(state) -> dict:
    print("  left")
    return {"values": ["left"]}


def right(state) -> dict:
    print("  right")
    return {"values": ["right"]}


def build(state_cls):
    g = StateGraph(state_cls)
    g.add_node("left", left)
    g.add_node("right", right)
    g.add_edge(START, "left")
    g.add_edge(START, "right")
    g.add_edge("left", END)
    g.add_edge("right", END)
    return g.compile()


def run_without_reducer():
    print("\n=== Without reducer (parallel writes to same field) ===")
    graph = build(BrokenState)
    for i in range(3):
        print(f"run {i + 1}:")
        try:
            print(f"  result: {graph.invoke({'values': []})}")
        except InvalidUpdateError as e:
            print(f"  InvalidUpdateError: {e}")


def run_with_reducer():
    print("\n=== With reducer (operator.add combines both writes) ===")
    graph = build(FixedState)
    for i in range(3):
        print(f"run {i + 1}:")
        result = graph.invoke({"values": []})
        print(f"  result: {result}")


if __name__ == "__main__":
    run_without_reducer()
    run_with_reducer()
