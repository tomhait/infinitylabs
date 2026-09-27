from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

llm = ChatOllama(model="llama3", temperature=0.7)
MAX_ATTEMPTS = 3


class State(TypedDict):
    draft: str
    attempts: int
    valid: bool
    sent: bool
    decision: str


def propose(state: State) -> dict:
    prompt = (
        "Propose a slogan about coffee. "
        "Reply with ONLY three words, nothing else."
    )
    draft = llm.invoke(prompt).content.strip().strip('"')
    attempts = state["attempts"] + 1
    print(f"  propose (attempt {attempts}): {draft!r}")
    return {"draft": draft, "attempts": attempts, "valid": False}


def validate(state: State) -> dict:
    words = [w for w in state["draft"].split() if w]
    ok = len(words) == 3
    print(f"  validate: {len(words)} words -> {'ok' if ok else 'fail'}")
    return {"valid": ok}


def route_after_validate(state: State):
    if state["valid"] or state["attempts"] >= MAX_ATTEMPTS:
        return "ok"
    return "propose"


def send(state: State) -> dict:
    print(f"  SENT (irreversible): {state['draft']!r}")
    return {"sent": True}


def human_review(state: State) -> dict:
    decision = interrupt(
        {
            "draft": state["draft"],
            "sent": state["sent"],
            "prompt": "approve or reject",
        }
    )
    print(f"  human: {decision}")
    return {"decision": decision}


def route_after_review(state: State):
    if state["decision"] == "approve":
        return "send"
    return END


def build(*, interrupt_before_send: bool):
    g = StateGraph(State)
    g.add_node("propose", propose)
    g.add_node("validate", validate)
    g.add_node("send", send)
    g.add_node("human_review", human_review)
    g.add_edge(START, "propose")
    g.add_edge("propose", "validate")
    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"propose": "propose", "ok": "human_review" if interrupt_before_send else "send"},
    )
    if interrupt_before_send:
        g.add_conditional_edges(
            "human_review",
            route_after_review,
            {"send": "send", END: END},
        )
        g.add_edge("send", END)
    else:
        g.add_edge("send", "human_review")
        g.add_edge("human_review", END)
    return g.compile(checkpointer=MemorySaver())


def run_until_interrupt(graph, config, inputs):
    result = graph.invoke(inputs, config)
    snap = graph.get_state(config)
    print(f"  paused: values={snap.values}, next={snap.next}")
    return result


def run_wrong_placement():
    print("\n=== Wrong: interrupt AFTER send (reject is too late) ===")
    graph = build(interrupt_before_send=False)
    config = {"configurable": {"thread_id": "wrong"}}
    run_until_interrupt(
        graph,
        config,
        {"draft": "", "attempts": 0, "valid": False, "sent": False, "decision": ""},
    )
    print(f"  already sent? {graph.get_state(config).values['sent']}")
    result = graph.invoke(Command(resume="reject"), config)
    print(f"  after reject: {result}")


def run_right_placement():
    print("\n=== Right: interrupt BEFORE send (reject prevents side-effect) ===")
    graph = build(interrupt_before_send=True)
    config = {"configurable": {"thread_id": "right"}}
    run_until_interrupt(
        graph,
        config,
        {"draft": "", "attempts": 0, "valid": False, "sent": False, "decision": ""},
    )
    print(f"  already sent? {graph.get_state(config).values['sent']}")
    result = graph.invoke(Command(resume="reject"), config)
    print(f"  after reject: {result}")


if __name__ == "__main__":
    run_wrong_placement()
    run_right_placement()
