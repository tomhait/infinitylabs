from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int
    fail: bool


def a(state: State) -> dict:
    print(f"  a: {state['value']} -> {state['value'] + 1}")
    return {"value": state["value"] + 1}


def b(state: State) -> dict:
    if state["fail"]:
        print(f"  b: crash at value={state['value']}")
        raise RuntimeError("simulated crash")
    print(f"  b: {state['value']} -> {state['value'] + 1}")
    return {"value": state["value"] + 1}


def c(state: State) -> dict:
    print(f"  c: {state['value']} -> {state['value'] + 1}")
    return {"value": state["value"] + 1}


def build():
    g = StateGraph(State)
    g.add_node("a", a)
    g.add_node("b", b)
    g.add_node("c", c)
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    g.add_edge("c", END)
    return g.compile(checkpointer=MemorySaver())


def run_crash_and_resume():
    print("\n=== Crash mid-run, then resume ===")
    graph = build()
    config = {"configurable": {"thread_id": "crash-demo"}}

    try:
        graph.invoke({"value": 0, "fail": True}, config)
    except RuntimeError as e:
        print(f"caught: {e}")

    snap = graph.get_state(config)
    print(f"checkpoint: values={snap.values}, next={snap.next}")

    graph.update_state(config, {"fail": False})
    result = graph.invoke(None, config)
    print(f"resumed: {result}")


def run_mutate_checkpoint():
    print("\n=== Mutate checkpoint outside a node ===")
    graph = build()
    config = {"configurable": {"thread_id": "mutate-demo"}}

    result = graph.invoke({"value": 0, "fail": False}, config)
    print(f"finished: {result}")

    graph.update_state(config, {"value": 99})
    snap = graph.get_state(config)
    print(f"mutated checkpoint: {snap.values}")

    result = graph.invoke(None, config)
    print(f"next invoke: {result}")
    print(f"final checkpoint: {graph.get_state(config).values}")


if __name__ == "__main__":
    run_crash_and_resume()
    run_mutate_checkpoint()
