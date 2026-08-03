import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from langchain_agent import LangChainAgent

MAX_ATTEMPTS = 3
AGENT_TASK = (
    "Compute (14 + 6) / 5 using the calculator tool. "
    "Then return final_answer with EXACTLY three words total: "
    "a coffee slogan where one of the three words is the number result. "
    "Example shape: Coffee 4 Power. "
    "Be creative."
)

agent = LangChainAgent(
    model="llama3.1",
    base_url="http://localhost:11434",
    timeout_seconds=60,
)


class State(TypedDict):
    draft: str
    attempts: int
    valid: bool
    sent: bool
    decision: str
    agent_messages: Annotated[list[str], operator.add]


def propose(state: State) -> dict:
    answer, scratch = agent.run_with_messages(AGENT_TASK, max_turns=6)
    draft = answer.strip().strip('"')
    attempts = state["attempts"] + 1
    print(f"  agent propose (attempt {attempts}): {draft!r}")
    for line in scratch:
        print(f"    {line}")
    return {
        "draft": draft,
        "attempts": attempts,
        "valid": False,
        "agent_messages": scratch,
    }


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


def build():
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
        {"propose": "propose", "ok": "human_review"},
    )
    g.add_conditional_edges(
        "human_review",
        route_after_review,
        {"send": "send", END: END},
    )
    g.add_edge("send", END)
    return g.compile(checkpointer=MemorySaver())


def main():
    print("\n=== Ex5: one ReAct agent node inside the graph ===")
    graph = build()
    config = {"configurable": {"thread_id": "ex5"}}
    graph.invoke(
        {
            "draft": "",
            "attempts": 0,
            "valid": False,
            "sent": False,
            "decision": "",
            "agent_messages": [],
        },
        config,
    )
    snap = graph.get_state(config)
    print(f"  paused: draft={snap.values['draft']!r}, sent={snap.values['sent']}")
    print(f"  agent_messages count: {len(snap.values['agent_messages'])}")
    result = graph.invoke(Command(resume="approve"), config)
    print(f"  after reject: draft={result['draft']!r}, sent={result['sent']}")


if __name__ == "__main__":
    main()
