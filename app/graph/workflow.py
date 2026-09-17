from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    classify_node,
    decide_node,
    draft_node,
    retrieve_policy_node,
    review_classification_node,
    review_escalation_node,
)
from app.graph.state import TicketState


def _after_classify(state: TicketState) -> str:
    return "retrieve_policy" if state.get("is_confident") else "review_classification"


def _after_decide(state: TicketState) -> str:
    return "review_escalation" if state.get("decision") == "escalate" else "draft"


def build_graph():
    g = StateGraph(TicketState)

    g.add_node("classify", classify_node)
    g.add_node("review_classification", review_classification_node)
    g.add_node("retrieve_policy", retrieve_policy_node)
    g.add_node("decide", decide_node)
    g.add_node("review_escalation", review_escalation_node)
    g.add_node("draft", draft_node)

    g.add_edge(START, "classify")

    g.add_conditional_edges(
        "classify",
        _after_classify,
        {
            "retrieve_policy": "retrieve_policy",
            "review_classification": "review_classification",
        },
    )

    g.add_edge("review_classification", "retrieve_policy")
    g.add_edge("retrieve_policy", "decide")

    g.add_conditional_edges(
        "decide",
        _after_decide,
        {
            "draft": "draft",
            "review_escalation": "review_escalation",
        },
    )

    g.add_conditional_edges(
        "review_escalation",
        lambda s: "draft" if s.get("decision") == "respond" else "end",
        {"draft": "draft", "end": END},
    )

    g.add_edge("draft", END)

    return g